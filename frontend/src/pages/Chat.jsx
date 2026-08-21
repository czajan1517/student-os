import { useEffect, useRef, useState } from "react";
import { Bot, LoaderCircle, Send, Sparkles } from "lucide-react";

import { sendChatMessage } from "../services/chatApi";


const INITIAL_MESSAGE = {
    id: "welcome-message",
    role: "assistant",
    content:
        "Hi! I can help you think through tasks, study plans, and schedules. " +
        "I cannot change StudentOS data yet.",
};


function createMessage(role, content) {
    return {
        id: crypto.randomUUID(),
        role,
        content,
    };
}


function Chat() {
    const [messages, setMessages] = useState([INITIAL_MESSAGE]);
    const [draft, setDraft] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState("");
    const messageEndRef = useRef(null);

    useEffect(() => {
        messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isSending]);

    async function handleSubmit(event) {
        event.preventDefault();
        const content = draft.trim();
        if (!content || isSending) {
            return;
        }

        const userMessage = createMessage("user", content);
        const nextMessages = [...messages, userMessage];
        setMessages(nextMessages);
        setDraft("");
        setError("");
        setIsSending(true);

        try {
            const response = await sendChatMessage(
                nextMessages.slice(-20).map(({ role, content: text }) => ({
                    role,
                    content: text,
                }))
            );
            setMessages((currentMessages) => [
                ...currentMessages,
                createMessage("assistant", response.message),
            ]);
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsSending(false);
        }
    }

    return (
        <section className="mx-auto flex h-[calc(100vh-4rem)] max-w-5xl flex-col">
            <header className="mb-6 flex items-start justify-between gap-6">
                <div>
                    <div className="mb-2 flex items-center gap-3">
                        <span className="flex size-11 items-center justify-center rounded-2xl bg-[#FFF0E5] text-[#C7651E]">
                            <Sparkles size={22} strokeWidth={1.9} />
                        </span>
                        <h1 className="text-3xl font-semibold tracking-tight text-[#241C17]">
                            StudentOS AI
                        </h1>
                    </div>
                    <p className="text-sm text-[#756960]">
                        Ask for planning and productivity guidance.
                    </p>
                </div>

                <span className="rounded-full border border-[#E8DED7] bg-white px-3 py-1.5 text-xs font-medium text-[#756960] shadow-sm">
                    Read-only preview
                </span>
            </header>

            <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl border border-[#E8DED7] bg-white shadow-[0_18px_50px_rgba(83,53,35,0.08)]">
                <div
                    className="flex-1 space-y-5 overflow-y-auto px-6 py-7 sm:px-8"
                    aria-live="polite"
                >
                    {messages.map((message) => {
                        const isUser = message.role === "user";

                        return (
                            <div
                                key={message.id}
                                className={`flex items-end gap-3 ${
                                    isUser ? "justify-end" : "justify-start"
                                }`}
                            >
                                {!isUser && (
                                    <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                                        <Bot size={18} strokeWidth={1.8} />
                                    </span>
                                )}

                                <div
                                    className={`max-w-[78%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 ${
                                        isUser
                                            ? "rounded-br-md bg-[#C7651E] text-white"
                                            : "rounded-bl-md bg-[#F7F3F0] text-[#3E342E]"
                                    }`}
                                >
                                    {message.content}
                                </div>
                            </div>
                        );
                    })}

                    {isSending && (
                        <div className="flex items-center gap-3 text-sm text-[#756960]">
                            <span className="flex size-9 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                                <LoaderCircle
                                    className="animate-spin"
                                    size={18}
                                    strokeWidth={1.8}
                                />
                            </span>
                            StudentOS AI is thinking…
                        </div>
                    )}

                    <div ref={messageEndRef} />
                </div>

                <div className="border-t border-[#EEE7E1] bg-[#FFFCFA] p-5 sm:p-6">
                    {error && (
                        <p
                            className="mb-3 rounded-xl border border-[#F3C7B0] bg-[#FFF2EB] px-4 py-2.5 text-sm text-[#A84E18]"
                            role="alert"
                        >
                            {error}
                        </p>
                    )}

                    <form
                        className="flex items-center gap-3"
                        onSubmit={handleSubmit}
                    >
                        <label className="sr-only" htmlFor="chat-message">
                            Message StudentOS AI
                        </label>
                        <input
                            id="chat-message"
                            className="min-w-0 flex-1 rounded-2xl border border-[#DED4CD] bg-white px-4 py-3 text-sm text-[#332A25] outline-none transition placeholder:text-[#A79C94] focus:border-[#C7651E] focus:ring-4 focus:ring-[#C7651E]/10"
                            type="text"
                            value={draft}
                            onChange={(event) => setDraft(event.target.value)}
                            placeholder="Ask about your tasks, schedule, or productivity…"
                            maxLength={4000}
                            disabled={isSending}
                            autoComplete="off"
                        />
                        <button
                            className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[#C7651E] text-white transition hover:bg-[#A95318] focus:outline-none focus:ring-4 focus:ring-[#C7651E]/20 disabled:cursor-not-allowed disabled:opacity-50"
                            type="submit"
                            disabled={!draft.trim() || isSending}
                            aria-label="Send message"
                        >
                            {isSending ? (
                                <LoaderCircle
                                    className="animate-spin"
                                    size={20}
                                />
                            ) : (
                                <Send size={20} strokeWidth={1.8} />
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </section>
    );
}

export default Chat;
