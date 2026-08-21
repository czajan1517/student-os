import { useEffect, useRef, useState } from "react";
import {
    Bot,
    Check,
    ClipboardList,
    LoaderCircle,
    MessageCircle,
    Send,
    Sparkles,
    X,
} from "lucide-react";

import {
    applyTaskCreation,
    previewTaskCreation,
    sendChatMessage,
} from "../services/chatApi";


const INITIAL_MESSAGE = {
    id: "welcome-message",
    role: "assistant",
    content:
        "Hi! I can help you think through tasks, study plans, and schedules. " +
        "Use Create task when you want me to prepare a task for confirmation.",
};


function createMessage(role, content) {
    return {
        id: crypto.randomUUID(),
        role,
        content,
    };
}


function TaskProposalCard({ proposal, isApplying, onConfirm, onCancel }) {
    const { task } = proposal;

    return (
        <div className="ml-12 max-w-2xl rounded-2xl border border-[#E8C9B5] bg-[#FFF8F3] p-5 text-sm text-[#3E342E] shadow-sm">
            <div className="mb-4 flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-full bg-[#FFE7D5] text-[#C7651E]">
                        <ClipboardList size={18} strokeWidth={1.8} />
                    </span>
                    <div>
                        <p className="font-semibold">Task creation preview</p>
                        <p className="text-xs text-[#80736A]">
                            Nothing has been saved yet.
                        </p>
                    </div>
                </div>
                <button
                    className="rounded-full p-1.5 text-[#80736A] transition hover:bg-white hover:text-[#3E342E]"
                    type="button"
                    onClick={onCancel}
                    aria-label="Cancel task proposal"
                >
                    <X size={17} />
                </button>
            </div>

            <dl className="grid gap-3 rounded-xl bg-white p-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                    <dt className="text-xs font-medium uppercase tracking-wide text-[#9A8D84]">
                        Title
                    </dt>
                    <dd className="mt-1 font-medium">{task.title}</dd>
                </div>
                <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-[#9A8D84]">
                        Estimated time
                    </dt>
                    <dd className="mt-1">
                        {task.estimated_time === null
                            ? "Needs your estimate"
                            : `${task.estimated_time} minutes`}
                    </dd>
                </div>
                <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-[#9A8D84]">
                        Task type
                    </dt>
                    <dd className="mt-1 capitalize">
                        {task.task_type.replaceAll("_", " ")}
                    </dd>
                </div>
                {task.due_date && (
                    <div className="sm:col-span-2">
                        <dt className="text-xs font-medium uppercase tracking-wide text-[#9A8D84]">
                            Due date
                        </dt>
                        <dd className="mt-1">
                            {new Date(task.due_date).toLocaleString()}
                        </dd>
                    </div>
                )}
                {task.description && (
                    <div className="sm:col-span-2">
                        <dt className="text-xs font-medium uppercase tracking-wide text-[#9A8D84]">
                            Description
                        </dt>
                        <dd className="mt-1 text-[#665A52]">
                            {task.description}
                        </dd>
                    </div>
                )}
            </dl>

            {proposal.follow_up_questions.length > 0 && (
                <div className="mt-4 rounded-xl border border-[#F0D5C4] bg-white px-4 py-3">
                    <p className="font-medium">More information needed</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-[#665A52]">
                        {proposal.follow_up_questions.map((question) => (
                            <li key={question}>{question}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="mt-4 flex justify-end gap-2">
                <button
                    className="rounded-xl border border-[#DED4CD] bg-white px-4 py-2 font-medium text-[#665A52] transition hover:bg-[#F8F4F1]"
                    type="button"
                    onClick={onCancel}
                    disabled={isApplying}
                >
                    Cancel
                </button>
                <button
                    className="flex items-center gap-2 rounded-xl bg-[#C7651E] px-4 py-2 font-medium text-white transition hover:bg-[#A95318] disabled:cursor-not-allowed disabled:opacity-50"
                    type="button"
                    onClick={onConfirm}
                    disabled={!proposal.ready_to_apply || isApplying}
                >
                    {isApplying ? (
                        <LoaderCircle className="animate-spin" size={17} />
                    ) : (
                        <Check size={17} />
                    )}
                    Confirm task
                </button>
            </div>
        </div>
    );
}


function Chat() {
    const [messages, setMessages] = useState([INITIAL_MESSAGE]);
    const [draft, setDraft] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [error, setError] = useState("");
    const [mode, setMode] = useState("chat");
    const [pendingProposal, setPendingProposal] = useState(null);
    const [pendingActionPrompt, setPendingActionPrompt] = useState("");
    const messageEndRef = useRef(null);

    useEffect(() => {
        messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isSending]);

    async function handleSubmit(event) {
        event.preventDefault();
        const content = draft.trim();
        if (!content || isSending || isApplying) {
            return;
        }

        const userMessage = createMessage("user", content);
        const nextMessages = [...messages, userMessage];
        setMessages(nextMessages);
        setDraft("");
        setError("");
        setIsSending(true);

        try {
            if (mode === "create_task") {
                const actionPrompt = pendingActionPrompt
                    ? `${pendingActionPrompt}\nAdditional information: ${content}`
                    : content;
                const proposal = await previewTaskCreation(actionPrompt);
                setPendingActionPrompt(actionPrompt);
                setPendingProposal(proposal);
            } else {
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
            }
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsSending(false);
        }
    }

    async function handleConfirmTask() {
        if (!pendingProposal?.ready_to_apply || isApplying) {
            return;
        }

        setError("");
        setIsApplying(true);
        try {
            const task = await applyTaskCreation(pendingProposal);
            setMessages((currentMessages) => [
                ...currentMessages,
                createMessage(
                    "assistant",
                    `Task created: ${task.title} (${task.estimated_time} minutes).`
                ),
            ]);
            setPendingProposal(null);
            setPendingActionPrompt("");
            setMode("chat");
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsApplying(false);
        }
    }

    function handleCancelTask() {
        setPendingProposal(null);
        setPendingActionPrompt("");
        setError("");
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
                    Task actions require confirmation
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

                    {pendingProposal && (
                        <TaskProposalCard
                            proposal={pendingProposal}
                            isApplying={isApplying}
                            onConfirm={handleConfirmTask}
                            onCancel={handleCancelTask}
                        />
                    )}

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

                    <div className="mb-3 flex gap-2" aria-label="AI mode">
                        <button
                            className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition ${
                                mode === "chat"
                                    ? "bg-[#C7651E] text-white"
                                    : "border border-[#DED4CD] bg-white text-[#665A52]"
                            }`}
                            type="button"
                            onClick={() => setMode("chat")}
                            disabled={isSending || isApplying}
                        >
                            <MessageCircle size={15} />
                            Ask AI
                        </button>
                        <button
                            className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition ${
                                mode === "create_task"
                                    ? "bg-[#C7651E] text-white"
                                    : "border border-[#DED4CD] bg-white text-[#665A52]"
                            }`}
                            type="button"
                            onClick={() => setMode("create_task")}
                            disabled={isSending || isApplying}
                        >
                            <ClipboardList size={15} />
                            Create task
                        </button>
                    </div>

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
                            placeholder={
                                mode === "create_task"
                                    ? "Describe the task you want to create..."
                                    : "Ask about your tasks, schedule, or productivity..."
                            }
                            maxLength={4000}
                            disabled={isSending || isApplying}
                            autoComplete="off"
                        />
                        <button
                            className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[#C7651E] text-white transition hover:bg-[#A95318] focus:outline-none focus:ring-4 focus:ring-[#C7651E]/20 disabled:cursor-not-allowed disabled:opacity-50"
                            type="submit"
                            disabled={!draft.trim() || isSending || isApplying}
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
