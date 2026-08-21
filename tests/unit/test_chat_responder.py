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
        client = FakeOllamaClient("Start with a focused 45-minute session.")
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
        self.assertTrue(
            call["messages"][1]["content"].endswith("/no_think")
        )
        self.assertEqual(
            call["options"],
            {"temperature": 0.3, "num_predict": 256},
        )
        self.assertIs(call["think"], False)
        self.assertNotIn("tools", call)

    def test_respond_rejects_an_empty_model_message(self):
        responder = ChatResponder(
            client=FakeOllamaClient("  "),
            model="test-chat-model",
        )

        with self.assertRaisesRegex(ChatResponseError, "did not return"):
            responder.respond(self.request())

    def test_respond_removes_model_thinking_from_the_visible_message(self):
        responder = ChatResponder(
            client=FakeOllamaClient(
                "I should reason about this first.</think>\n\n"
                "Here is the useful answer."
            ),
            model="test-chat-model",
        )

        result = responder.respond(self.request())

        self.assertEqual(result.message, "Here is the useful answer.")

    def test_model_override_is_resolved_from_environment(self):
        client = FakeOllamaClient("Use the environment model.")
        responder = ChatResponder(client=client)

        with patch.dict("os.environ", {"OLLAMA_CHAT_MODEL": "local-model"}):
            responder.respond(self.request())

        self.assertEqual(client.calls[0]["model"], "local-model")

    def test_latest_chat_message_must_come_from_the_user(self):
        with self.assertRaisesRegex(ValidationError, "latest chat message"):
            ChatRequest(
                messages=[
                    ChatMessage(role="assistant", content="How can I help?")
                ]
            )


if __name__ == "__main__":
    unittest.main()
