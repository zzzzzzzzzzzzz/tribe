import base64
import mimetypes
import os
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from gigachat import GigaChat
from openai import OpenAI
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    ChatContentFilePart,
    ChatContentImagePart,
    ChatMessage,
    Member,
    ProviderAttachment,
)

ProviderName = Literal["openai", "gigachat"]
ProviderFileIds = dict[ProviderName, list[str]]
OpenAIFilePurpose = Literal["vision", "user_data"]
SUPPORTED_IMAGE_TYPES = {"image/gif", "image/jpeg", "image/png", "image/webp"}
SUPPORTED_FILE_TYPES = {
    "application/json",
    "application/pdf",
    "text/csv",
    "text/markdown",
    "text/plain",
}
SUPPORTED_ATTACHMENT_TYPES = SUPPORTED_IMAGE_TYPES | SUPPORTED_FILE_TYPES


def _parse_data_url(data_url: str) -> tuple[str, bytes] | None:
    if not data_url.startswith("data:"):
        return None
    try:
        metadata, payload = data_url.split(",", 1)
    except ValueError:
        return None

    if ";base64" not in metadata:
        return None

    mime_type = metadata.split(":", 1)[1].split(";", 1)[0]
    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception:
        return None
    return mime_type, decoded


def _openai_file_purpose(
    *, filename: str, content_type: str | None
) -> OpenAIFilePurpose:
    guessed_type = mimetypes.guess_type(filename)[0]
    effective_type = content_type or guessed_type
    if effective_type and effective_type.startswith("image/"):
        return "vision"
    return "user_data"


def _is_supported_attachment_type(content_type: str | None) -> bool:
    return content_type in SUPPORTED_ATTACHMENT_TYPES


def _upload_to_openai(
    *,
    content: bytes,
    filename: str,
    content_type: str | None,
    base_url: str | None,
) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key, base_url=base_url)
    purpose = _openai_file_purpose(filename=filename, content_type=content_type)
    uploaded = client.files.create(file=(filename, content), purpose=purpose)
    return uploaded.id


def _upload_to_gigachat(
    *, content: bytes, filename: str, content_type: str | None, base_url: str | None
) -> str | None:
    token = os.getenv("GIGACHAT_AUTH_TOKEN")
    if not token:
        return None

    client = GigaChat(
        credentials=token,
        base_url=base_url,
        verify_ssl_certs=False,
    )
    uploaded = client.upload_file((filename, content), purpose="general")
    return getattr(uploaded, "id_", None) or getattr(uploaded, "id", None)


def delete_provider_file(
    *, provider_name: ProviderName, file_id: str, base_url: str | None
) -> None:
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return
        OpenAI(api_key=api_key, base_url=base_url).files.delete(file_id)
        return

    token = os.getenv("GIGACHAT_AUTH_TOKEN")
    if not token:
        return
    GigaChat(
        credentials=token,
        base_url=base_url,
        verify_ssl_certs=False,
    ).delete_file(file_id)


def cleanup_provider_files(
    *, provider_file_ids: ProviderFileIds, members: Iterable[Member]
) -> None:
    provider_base_urls = _target_provider_configs(members)
    for provider_name, provider_base_url in provider_base_urls:
        for file_id in provider_file_ids.get(provider_name, []):
            try:
                delete_provider_file(
                    provider_name=provider_name,
                    file_id=file_id,
                    base_url=provider_base_url,
                )
            except Exception:
                continue


def collect_provider_file_ids(message: ChatMessage) -> ProviderFileIds:
    provider_file_ids: ProviderFileIds = {"openai": [], "gigachat": []}
    if isinstance(message.content, str):
        return provider_file_ids

    for part in message.content:
        if isinstance(part, ChatContentFilePart):
            part_provider_ids = part.file.provider_file_ids or {}
        elif isinstance(part, ChatContentImagePart):
            part_provider_ids = part.image_url.provider_file_ids or {}
        else:
            continue

        for provider_name in ("openai", "gigachat"):
            provider_file_id = part_provider_ids.get(provider_name)
            if isinstance(provider_file_id, str) and provider_file_id:
                provider_file_ids[provider_name].append(provider_file_id)

    return provider_file_ids


def merge_provider_file_ids(
    provider_file_ids: Iterable[ProviderFileIds],
) -> ProviderFileIds:
    merged: ProviderFileIds = {"openai": [], "gigachat": []}
    for item in provider_file_ids:
        for provider_name in ("openai", "gigachat"):
            for file_id in item.get(provider_name, []):
                if file_id not in merged[provider_name]:
                    merged[provider_name].append(file_id)
    return merged


def persist_provider_attachments(
    *, thread_id: str, messages: Iterable[ChatMessage], members: Iterable[Member]
) -> None:
    provider_base_urls = _target_provider_configs(members)
    expires_at = datetime.now(ZoneInfo("UTC")) + timedelta(days=30)
    with Session(engine) as session:
        for message in messages:
            if isinstance(message.content, str):
                continue

            for part in message.content:
                if isinstance(part, ChatContentFilePart):
                    provider_ids = part.file.provider_file_ids or {}
                    file_data = part.file.file_data
                    filename = part.file.filename or "attachment.bin"
                elif isinstance(part, ChatContentImagePart):
                    provider_ids = part.image_url.provider_file_ids or {}
                    file_data = part.image_url.url
                    filename = "image.png"
                else:
                    continue

                content_type = None
                if isinstance(file_data, str):
                    parsed = _parse_data_url(file_data)
                    if parsed:
                        content_type = parsed[0]

                for provider_name, provider_base_url in provider_base_urls:
                    file_id = provider_ids.get(provider_name)
                    if not file_id:
                        continue

                    existing = session.exec(
                        select(ProviderAttachment).where(
                            ProviderAttachment.provider == provider_name,
                            ProviderAttachment.file_id == file_id,
                        )
                    ).first()
                    if existing:
                        existing.expires_at = expires_at
                        existing.deleted_at = None
                        session.add(existing)
                        continue

                    session.add(
                        ProviderAttachment(
                            thread_id=UUID(thread_id),
                            provider=provider_name,
                            file_id=file_id,
                            filename=filename,
                            content_type=content_type,
                            base_url=provider_base_url,
                            expires_at=expires_at,
                        )
                    )

        session.commit()


def _target_provider_configs(
    members: Iterable[Member],
) -> set[tuple[ProviderName, str | None]]:
    targets: set[tuple[ProviderName, str | None]] = set()
    for member in members:
        if member.provider == "openai":
            targets.add(("openai", member.base_url))
        if member.provider == "gigachat":
            targets.add(("gigachat", member.base_url))
    return targets


def upload_attachments_for_thread(
    *, message: ChatMessage, members: list[Member]
) -> ChatMessage:
    if isinstance(message.content, str):
        return message

    provider_targets = _target_provider_configs(members)
    if not provider_targets:
        return message

    for part in message.content:
        file_data: str | None = None
        filename = "attachment.bin"

        if isinstance(part, ChatContentFilePart):
            if isinstance(part.file.filename, str) and part.file.filename:
                filename = part.file.filename
            file_data = part.file.file_data
            provider_ids = part.file.provider_file_ids or {}
        elif isinstance(part, ChatContentImagePart):
            file_data = part.image_url.url
            provider_ids = part.image_url.provider_file_ids or {}
            filename = "image.png"
        else:
            continue

        if isinstance(part, ChatContentFilePart):
            part.file.provider_file_ids = provider_ids
        elif isinstance(part, ChatContentImagePart):
            part.image_url.provider_file_ids = provider_ids

        if not isinstance(file_data, str):
            continue

        parsed = _parse_data_url(file_data)
        if not parsed:
            continue
        content_type, content = parsed
        if not _is_supported_attachment_type(content_type):
            continue

        for provider_name, provider_base_url in provider_targets:
            if provider_name in provider_ids:
                continue

            remote_id: str | None = None
            if provider_name == "openai":
                remote_id = _upload_to_openai(
                    content=content,
                    filename=filename,
                    content_type=content_type,
                    base_url=provider_base_url,
                )
            elif provider_name == "gigachat":
                remote_id = _upload_to_gigachat(
                    content=content,
                    filename=filename,
                    content_type=content_type,
                    base_url=provider_base_url,
                )

            if not remote_id:
                continue

            provider_ids[provider_name] = remote_id
            if isinstance(part, ChatContentFilePart):
                part.file.provider_file_ids = provider_ids
                if provider_name == "openai":
                    part.file.file_id = remote_id
            elif isinstance(part, ChatContentImagePart):
                part.image_url.provider_file_ids = provider_ids

    return message
