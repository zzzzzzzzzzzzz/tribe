from collections.abc import Sequence
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from sqlmodel import col, func, or_, select

from app.api.deps import (
    CurrentTeam,
    CurrentUser,
    SessionDep,
)
from app.core.graph.build import generator
from app.models import (
    ChatContentFilePart,
    ChatContentImagePart,
    ChatContentTextPart,
    Member,
    Message,
    Skill,
    Team,
    TeamChat,
    TeamChatPublic,
    TeamCreate,
    TeamExport,
    TeamExportMember,
    TeamExportSkillRef,
    TeamExportUploadRef,
    TeamOut,
    TeamsOut,
    TeamUpdate,
    Thread,
    Upload,
    User,
)

router = APIRouter()

header_scheme = APIKeyHeader(name="x-api-key")


async def validate_name_on_create(session: SessionDep, team_in: TeamCreate) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name)
    team = session.exec(statement).first()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


async def validate_name_on_update(
    session: SessionDep, team_in: TeamUpdate, id: int
) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name, Team.id != id)
    team = session.exec(statement).first()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


def _extract_text_content(
    content: str
    | Sequence[ChatContentTextPart | ChatContentImagePart | ChatContentFilePart],
) -> str:
    if isinstance(content, str):
        return content
    text_parts: list[str] = []
    for part in content:
        if not hasattr(part, "model_dump"):
            continue
        dumped = part.model_dump()
        if dumped.get("type") == "text":
            text = dumped.get("text")
            if isinstance(text, str):
                text_parts.append(text)
    return "\n".join(text_parts)


def _unique_team_name(session: SessionDep, name: str) -> str:
    existing = session.exec(select(Team).where(Team.name == name)).first()
    if not existing:
        return name

    base = name[:55].rstrip() or "Imported team"
    for index in range(2, 1000):
        candidate = f"{base} {index}"
        if not session.exec(select(Team).where(Team.name == candidate)).first():
            return candidate

    raise HTTPException(status_code=400, detail="Unable to generate unique team name")


def _can_read_team(current_user: User, team: Team) -> bool:
    return current_user.is_superuser or team.owner_id == current_user.id


def _skill_ref(skill: Skill) -> TeamExportSkillRef:
    return TeamExportSkillRef(
        name=skill.name,
        description=skill.description,
        managed=skill.managed,
        tool_definition=skill.tool_definition,
    )


def _upload_ref(upload: Upload) -> TeamExportUploadRef:
    return TeamExportUploadRef(name=upload.name, description=upload.description)


def _member_export(member: Member) -> TeamExportMember:
    return TeamExportMember(
        id=member.id or 0,
        name=member.name,
        backstory=member.backstory,
        role=member.role,
        type=member.type,
        owner_of=member.owner_of,
        position_x=member.position_x,
        position_y=member.position_y,
        source=member.source,
        provider=member.provider,
        model=member.model,
        temperature=member.temperature,
        interrupt=member.interrupt,
        base_url=member.base_url,
        skills=[_skill_ref(skill) for skill in member.skills],
        uploads=[_upload_ref(upload) for upload in member.uploads],
    )


def _accessible_skills_by_name(
    session: SessionDep, current_user: User
) -> dict[str, Skill]:
    if current_user.is_superuser:
        skills = session.exec(select(Skill)).all()
    else:
        skills = session.exec(
            select(Skill).where(
                or_(Skill.managed == True, Skill.owner_id == current_user.id)  # noqa: E712
            )
        ).all()
    return {skill.name: skill for skill in skills}


def _accessible_uploads_by_name(
    session: SessionDep, current_user: User
) -> dict[str, Upload]:
    if current_user.is_superuser:
        uploads = session.exec(select(Upload)).all()
    else:
        uploads = session.exec(
            select(Upload).where(Upload.owner_id == current_user.id)
        ).all()
    return {upload.name: upload for upload in uploads}


@router.get("/", response_model=TeamsOut)
def read_teams(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve teams
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Team)
        count = session.exec(count_statement).one()
        statement = select(Team).offset(skip).limit(limit).order_by(col(Team.id).desc())
        teams = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Team)
            .where(Team.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Team)
            .where(Team.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .order_by(col(Team.id).desc())
        )
        teams = session.exec(statement).all()
    return TeamsOut(data=teams, count=count)


@router.get("/{id}", response_model=TeamOut)
def read_team(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Get team by ID.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not current_user.is_superuser and (team.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return team


@router.post("/", response_model=TeamOut)
def create_team(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    team_in: TeamCreate,
    _: bool = Depends(validate_name_on_create),
) -> Any:
    """
    Create new team and it's team leader
    """
    team = Team.model_validate(team_in, update={"owner_id": current_user.id})
    session.add(team)
    session.commit()

    if team.workflow == "hierarchical":
        # Create team leader
        member = Member(
            # The leader name will be used as the team's name in the graph, so it has to be specific
            name=f"{team.name}Leader",
            type="root",
            role="Gather inputs from your team and answer the question.",
            owner_of=team.id,
            position_x=0,
            position_y=0,
            belongs_to=team.id,
        )
    else:
        # Create a freelancer head
        member = Member(
            name="Worker0",
            type="freelancer_root",
            role="Answer the user's question.",
            owner_of=None,
            position_x=0,
            position_y=0,
            belongs_to=team.id,
        )
    session.add(member)
    session.commit()

    return team


@router.post("/import", response_model=TeamOut)
def import_team(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    team_export: TeamExport,
) -> Any:
    """
    Import a team definition and create a new team.
    Missing skills and uploads are ignored.
    """
    team = Team(
        name=_unique_team_name(session, team_export.name),
        description=team_export.description,
        workflow=team_export.workflow,
        owner_id=current_user.id,
    )
    session.add(team)
    session.commit()
    session.refresh(team)

    skills_by_name = _accessible_skills_by_name(session, current_user)
    uploads_by_name = _accessible_uploads_by_name(session, current_user)
    member_id_map: dict[int, int] = {}
    imported_members: list[tuple[Member, TeamExportMember]] = []

    for member_export in team_export.members:
        member = Member(
            name=member_export.name,
            backstory=member_export.backstory,
            role=member_export.role,
            type=member_export.type,
            owner_of=None,
            position_x=member_export.position_x,
            position_y=member_export.position_y,
            source=None,
            provider=member_export.provider,
            model=member_export.model,
            temperature=member_export.temperature,
            interrupt=member_export.interrupt,
            base_url=member_export.base_url,
            belongs_to=team.id,
        )
        member.skills = [
            skills_by_name[skill.name]
            for skill in member_export.skills
            if skill.name in skills_by_name
        ]
        member.uploads = [
            uploads_by_name[upload.name]
            for upload in member_export.uploads
            if upload.name in uploads_by_name
        ]
        session.add(member)
        session.commit()
        session.refresh(member)
        if member.id is not None:
            member_id_map[member_export.id] = member.id
        imported_members.append((member, member_export))

    for member, member_export in imported_members:
        if member_export.source is not None:
            member.source = member_id_map.get(member_export.source)
        if member_export.owner_of == team_export.id:
            member.owner_of = team.id
        elif member_export.owner_of is not None:
            member.owner_of = member_id_map.get(member_export.owner_of)
        session.add(member)

    session.commit()
    session.refresh(team)
    return team


@router.get("/{id}/export", response_model=TeamExport)
def export_team(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Export a team definition including members and graph settings.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not _can_read_team(current_user, team):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return TeamExport(
        id=team.id,
        name=team.name,
        description=team.description,
        workflow=team.workflow,
        members=[
            _member_export(member)
            for member in sorted(team.members, key=lambda item: item.id or 0)
        ],
    )


@router.put("/{id}", response_model=TeamOut)
def update_team(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    team_in: TeamUpdate,
    _: bool = Depends(validate_name_on_update),
) -> Any:
    """
    Update a team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not current_user.is_superuser and (team.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = team_in.model_dump(exclude_unset=True)
    team.sqlmodel_update(update_dict)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


@router.delete("/{id}")
def delete_team(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Delete a team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not current_user.is_superuser and (team.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(team)
    session.commit()
    return Message(message="Team deleted successfully")


@router.post("/{id}/stream/{thread_id}")
async def stream(
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    thread_id: str,
    team_chat: TeamChat,
) -> StreamingResponse:
    """
    Stream a response to a user's input.
    """
    # Get team and join members and skills
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not current_user.is_superuser and (team.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Check if thread belongs to the team
    thread = session.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread.team_id != id:
        raise HTTPException(
            status_code=400, detail="Thread does not belong to the team"
        )

    # Populate the skills and accessible uploads for each member
    members = team.members
    for member in members:
        member.skills = member.skills
        member.uploads = member.uploads

    return StreamingResponse(
        generator(team, members, team_chat.messages, thread_id, team_chat.interrupt),
        media_type="text/event-stream",
    )


@router.post("/{team_id}/stream-public/{thread_id}")
async def public_stream(
    session: SessionDep,
    team_id: int,
    team_chat: TeamChatPublic,
    thread_id: str,
    team: CurrentTeam,
    streaming: bool = True,
) -> StreamingResponse:
    """
    Stream a response from a team using a given message or an interrupt decision. Requires an API key for authentication.

    This endpoint allows streaming responses from a team based on a provided message or interrupt details. The request must include an API key for authorization.

    Parameters:
    - `team_id` (int): The ID of the team to which the message is being sent. Must be a valid team ID.
    - `thread_id` (str): The ID of the thread where the message will be posted. If the thread ID does not exist, a new thread will be created.
    - `streaming` (bool, optional): A flag to enable or disable streaming mode. If `True` (default), the messages will be streamed in chunks.

    Request Body (JSON):
    - The request body should be a JSON object containing either the `message` or `interrupt` field:
        - `message` (object, optional): The message to be sent to the team.
            - `type` (str): Must be `"human"`.
            - `content` (str): The content of the message to be sent.
        - `interrupt` (object, optional): Approve/reject tool or reply to an ask-human tool.
            - `decision` (str): Can be `'approved'`, `'rejected'`, or `'replied'`.
            - `tool_message` (str or null, optional): If `decision` is `'rejected'` or `'replied'`, provide a message explaining the reason for rejection or the reply.

    Authorization:
    - API key must be provided in the request header as `x-api-key`.

    Responses:
    - `200 OK`: Returns a streaming response in `text/event-stream` format containing the team's response.
    """
    # Check if thread belongs to the team
    thread = session.get(Thread, thread_id)
    message_content = (
        _extract_text_content(team_chat.message.content) if team_chat.message else ""
    )
    if not thread:
        # create new thread
        thread = Thread(
            id=thread_id,
            query=message_content,
            updated_at=datetime.now(),
            team_id=team_id,
        )
        session.add(thread)
        session.commit()
        session.refresh(thread)
    else:
        if thread.team_id != team_id:
            raise HTTPException(
                status_code=400, detail="Thread does not belong to the team"
            )

    # Populate the skills and accessible uploads for each member
    members = team.members
    for member in members:
        member.skills = member.skills
        member.uploads = member.uploads

    messages = [team_chat.message] if team_chat.message else []
    return StreamingResponse(
        generator(team, members, messages, thread_id, team_chat.interrupt, streaming),
        media_type="text/event-stream",
    )
