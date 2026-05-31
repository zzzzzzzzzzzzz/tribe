from langchain_core.messages import AnyMessage, HumanMessage

from app.core.graph.members import (
    LeaderNode,
    SummariserNode,
    WorkerNode,
    format_messages,
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
