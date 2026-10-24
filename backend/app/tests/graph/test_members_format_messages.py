from typing import cast

from langchain_core.messages import AnyMessage, HumanMessage

from app.core.graph.members import (
    LeaderNode,
    SummariserNode,
    TeamState,
    WorkerNode,
    format_messages,
    previous_attachment_messages,
)


def test_format_messages_hides_binary_attachment_payloads() -> None:
    messages: list[AnyMessage] = [
        HumanMessage(
            name="user",
            content=[
                {"type": "text", "text": "Please analyze"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,AAAAAA"},
                },
                {
                    "type": "file",
                    "file": {
                        "filename": "report.pdf",
                        "file_data": "data:application/pdf;base64,BBBBBB",
                    },
                },
            ],
        )
    ]

    result = format_messages(messages)

    assert "Please analyze" in result
    assert "[Attached image]" in result
    assert "[Attached file: report.pdf]" in result
    assert "base64" not in result


def test_format_messages_handles_openai_input_parts() -> None:
    messages: list[AnyMessage] = [
        HumanMessage(
            name="user",
            content=[
                {"type": "input_text", "text": "What is in this contract?"},
                {"type": "input_image", "image_url": "data:image/png;base64,AAAAAA"},
                {
                    "type": "input_file",
                    "filename": "contract.pdf",
                    "file_data": "data:application/pdf;base64,BBBBBB",
                },
            ],
        )
    ]

    result = format_messages(messages)

    assert "What is in this contract?" in result
    assert "[Attached image]" in result
    assert "[Attached file: contract.pdf]" in result
    assert "base64" not in result


def test_worker_prompt_includes_native_attachment_context_message() -> None:
    context_message = HumanMessage(
        name="user",
        content=[
            {"type": "input_text", "text": "Inspect this file"},
            {"type": "input_image", "file_id": "image-file-id"},
        ],
    )

    prompt_value = WorkerNode.worker_prompt.invoke(
        {
            "team_name": "Team",
            "team_members_name": "Expert",
            "persona": "Role",
            "task_string": "Ответь по сути",
            "history_string": "user: Inspect this file",
            "main_task": [context_message],
            "messages": [],
        }
    )
    messages = prompt_value.to_messages()

    assert any(
        isinstance(message.content, str)
        and "только как дополнительный контекст" in message.content
        for message in messages
    )
    assert messages[-1].content == context_message.content


def test_leader_and_summariser_prompts_include_native_attachment_context() -> None:
    context_message = HumanMessage(
        name="user",
        content=[
            {"type": "input_text", "text": "Inspect this file"},
            {"type": "input_file", "file_id": "file-id"},
        ],
    )

    leader_messages = LeaderNode.leader_prompt.invoke(
        {
            "team_name": "Team",
            "team_members_name": "Leader",
            "team_members_info": "name: Expert\nrole: Analyst",
            "persona": "Lead",
            "team_task": "Inspect this file",
            "history_string": "user: Inspect this file",
            "options": "['Expert', 'FINISH']",
            "main_task": [context_message],
        }
    ).to_messages()
    summariser_messages = SummariserNode.summariser_prompt.invoke(
        {
            "team_name": "Team",
            "team_members_name": "Expert",
            "team_task": "Inspect this file",
            "history_string": "Expert: Done",
            "main_task": [context_message],
        }
    ).to_messages()

    assert leader_messages[-1].content == context_message.content
    assert summariser_messages[-1].content == context_message.content
    assert any(
        isinstance(message.content, str) and "Это только контекст" in message.content
        for message in leader_messages
    )
    assert any(
        isinstance(message.content, str) and "только как контекст" in message.content
        for message in summariser_messages
    )


def test_openai_second_turn_reuses_uploaded_image_and_document_ids() -> None:
    state = cast(
        TeamState,
        {
            "main_task": [HumanMessage(content="А что было на той картинке?")],
            "historical_provider_attachments": {
                "openai": [
                    {"kind": "image", "file_id": "openai-image-1", "filename": "x.png"},
                    {"kind": "file", "file_id": "openai-file-1", "filename": "a.pdf"},
                ]
            },
        },
    )
    messages = previous_attachment_messages(state, "openai")
    assert [message.content for message in messages] == [
        [
            {
                "type": "input_text",
                "text": "Ранее прикреплённое изображение пользователя",
            },
            {"type": "input_image", "file_id": "openai-image-1"},
        ],
        [
            {"type": "input_text", "text": "Ранее прикреплённый документ: a.pdf"},
            {"type": "input_file", "file_id": "openai-file-1"},
        ],
    ]
    assert all("base64" not in str(message.content) for message in messages)


def test_gigachat_second_turn_uses_existing_attachments() -> None:
    state = cast(
        TeamState,
        {
            "main_task": [HumanMessage(content="Помнишь изображение?")],
            "historical_provider_attachments": {
                "gigachat": [
                    {"kind": "image", "file_id": "giga-image-1", "filename": "a.jpg"}
                ]
            },
        },
    )
    messages = previous_attachment_messages(state, "gigachat")
    assert len(messages) == 1
    assert messages[0].additional_kwargs == {"attachments": ["giga-image-1"]}
    assert isinstance(messages[0].content, str)


def test_gigachat_respects_ten_image_limit_with_current_images() -> None:
    state = cast(
        TeamState,
        {
            "main_task": [
                HumanMessage(
                    content=[
                        {"type": "image_url", "image_url": {"url": "one"}},
                        {"type": "image_url", "image_url": {"url": "two"}},
                    ]
                )
            ],
            "historical_provider_attachments": {
                "gigachat": [
                    {"kind": "image", "file_id": f"old-{index}", "filename": "x.png"}
                    for index in range(12)
                ]
            },
        },
    )
    messages = previous_attachment_messages(state, "gigachat")
    assert len(messages) == 8
    assert messages[0].additional_kwargs["attachments"] == ["old-4"]
    assert messages[-1].additional_kwargs["attachments"] == ["old-11"]


def test_sequential_worker_prompt_contains_previous_attachment_before_new_task() -> (
    None
):
    history_message = HumanMessage(
        content=[
            {"type": "input_text", "text": "Previous attachment"},
            {"type": "input_image", "file_id": "image-1"},
        ]
    )
    new_message = HumanMessage(content="What color was it?")
    prompt = WorkerNode.worker_prompt.invoke(
        {
            "team_name": "Team",
            "team_members_name": "Analyst",
            "persona": "Role",
            "task_string": "Answer",
            "history_string": "user: sent image",
            "previous_attachments": [history_message],
            "main_task": [new_message],
            "messages": [],
        }
    )
    messages = prompt.to_messages()
    assert messages[-2].content == history_message.content
    assert messages[-1].content == new_message.content
