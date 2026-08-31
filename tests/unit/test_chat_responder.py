import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.ai.chat_responder import ChatResponder, ChatResponseError
from backend.schemas.ai import ChatMessage, ChatRequest


class FakeOllamaClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.content


class ChatResponderTests(unittest.TestCase):
    def request(self):
        return ChatRequest(
            messages=[
                ChatMessage(role="user", content="Help me plan a study session")
            ]
        )

    def test_respond_returns_text_without_application_tools(self):
        client = FakeOllamaClient(
            "Start with a focused 45-minute session."
        )
        responder = ChatResponder(client=client, model="test-chat-model")

        result = responder.respond(self.request())

        self.assertEqual(
            result.message,
            "Start with a focused 45-minute session.",
        )
        call = client.calls[0]
        self.assertEqual(call["model"], "test-chat-model")
        self.assertEqual(call["messages"][0]["role"], "system")
        self.assertEqual(call["messages"][1]["role"], "user")
        self.assertEqual(
            call["messages"][1]["content"],
            "Help me plan a study session",
        )
        self.assertNotIn("output_format", call)
        self.assertEqual(
            call["options"],
            {"temperature": 0.3, "num_predict": 512},
        )
        self.assertIn(
            "Always provide a complete answer",
            call["messages"][0]["content"],
        )
        self.assertNotIn("think", call)
        self.assertNotIn("tools", call)

    def test_respond_rejects_an_empty_model_message(self):
        responder = ChatResponder(
            client=FakeOllamaClient("  "),
            model="test-chat-model",
        )

        with self.assertRaisesRegex(ChatResponseError, "safe final answer"):
            responder.respond(self.request())

    def test_respond_rejects_untagged_reasoning(self):
        responder = ChatResponder(
            client=FakeOllamaClient(
                "Okay, the user is asking for a study plan. Let me think "
                "about the rules and how I should structure the response."
            ),
            model="test-chat-model",
        )

        with self.assertRaisesRegex(
            ChatResponseError,
            "safe final answer",
        ):
            responder.respond(self.request())

    def test_respond_rejects_thinking_tags(self):
        responder = ChatResponder(
            client=FakeOllamaClient(
                "<think>Internal planning that must not be shown.</think>\n\n"
                "Use two focused 50-minute blocks."
            ),
            model="test-chat-model",
        )

        with self.assertRaisesRegex(
            ChatResponseError,
            "safe final answer",
        ):
            responder.respond(self.request())

    def test_model_override_is_resolved_from_environment(self):
        client = FakeOllamaClient(
            "Use the environment model."
        )
        responder = ChatResponder(client=client)

        with patch.dict("os.environ", {"OLLAMA_CHAT_MODEL": "local-model"}):
            responder.respond(self.request())

        self.assertEqual(client.calls[0]["model"], "local-model")

    def test_default_chat_model_is_the_lightweight_local_model(self):
        responder = ChatResponder(client=FakeOllamaClient("unused"))

        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(responder.model, "llama3.2:1b")

    def test_latest_chat_message_must_come_from_the_user(self):
        with self.assertRaisesRegex(ValidationError, "latest chat message"):
            ChatRequest(
                messages=[
                    ChatMessage(role="assistant", content="How can I help?")
                ]
            )


if __name__ == "__main__":
    unittest.main()
