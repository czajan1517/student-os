import { useEffect, useState } from "react";

import {
    applyTaskCreation,
    previewTaskCreation,
    sendChatMessage,
} from "../services/chatApi";
import ChatContext from "./chatContext";


const INITIAL_MESSAGE = {
    id: "welcome-message",
    role: "assistant",
    content:
        "Hi! I can help you think through tasks, study plans, and schedules. " +
        "Use Create task when you want me to prepare a task for confirmation.",
};

const CHAT_HISTORY_STORAGE_KEY = "studentos.chat.messages";
const CHAT_MODE_STORAGE_KEY = "studentos.chat.mode";
const TASK_PROPOSAL_STORAGE_KEY = "studentos.chat.pendingTaskProposal";


function readStoredJson(key) {
    try {
        return JSON.parse(localStorage.getItem(key));
    } catch {
        return null;
    }
}


function loadStoredMessages() {
    const storedMessages = readStoredJson(CHAT_HISTORY_STORAGE_KEY);
    if (!Array.isArray(storedMessages) || storedMessages.length === 0) {
        return [INITIAL_MESSAGE];
    }

    const validMessages = storedMessages.filter(
        (message) =>
            typeof message?.id === "string" &&
            (message.role === "user" || message.role === "assistant") &&
            typeof message.content === "string"
    );

    return validMessages.length ? validMessages : [INITIAL_MESSAGE];
}


function loadStoredMode() {
    return localStorage.getItem(CHAT_MODE_STORAGE_KEY) === "create_task"
        ? "create_task"
        : "chat";
}


function loadStoredProposal() {
    const proposal = readStoredJson(TASK_PROPOSAL_STORAGE_KEY);
    const task = proposal?.task;
    const schedule = proposal?.schedule_preview;

    if (
        typeof proposal?.ready_to_apply !== "boolean" ||
        !Array.isArray(proposal?.follow_up_questions) ||
        typeof task?.title !== "string" ||
        typeof task?.task_type !== "string" ||
        (schedule !== null &&
            schedule !== undefined &&
            (!Array.isArray(schedule.proposed_blocks) ||
                !Array.isArray(schedule.warnings)))
    ) {
        return null;
    }

    return proposal;
}


function createMessage(role, content) {
    return {
        id: crypto.randomUUID(),
        role,
        content,
    };
}


function ChatProvider({ children }) {
    const [messages, setMessages] = useState(loadStoredMessages);
    const [isSending, setIsSending] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [error, setError] = useState("");
    const [mode, setMode] = useState(loadStoredMode);
    const [pendingProposal, setPendingProposal] = useState(loadStoredProposal);

    useEffect(() => {
        localStorage.setItem(
            CHAT_HISTORY_STORAGE_KEY,
            JSON.stringify(messages)
        );
    }, [messages]);

    useEffect(() => {
        localStorage.setItem(CHAT_MODE_STORAGE_KEY, mode);
    }, [mode]);

    useEffect(() => {
        if (pendingProposal) {
            localStorage.setItem(
                TASK_PROPOSAL_STORAGE_KEY,
                JSON.stringify(pendingProposal)
            );
        } else {
            localStorage.removeItem(TASK_PROPOSAL_STORAGE_KEY);
        }
    }, [pendingProposal]);

    async function submitMessage(content) {
        const cleanContent = content.trim();
        if (!cleanContent || isSending || isApplying) {
            return;
        }

        const userMessage = createMessage("user", cleanContent);
        const nextMessages = [...messages, userMessage];
        setMessages(nextMessages);
        setError("");
        setIsSending(true);

        try {
            if (mode === "create_task") {
                const proposal = await previewTaskCreation(
                    cleanContent,
                    pendingProposal
                );
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

    async function confirmTask() {
        if (!pendingProposal?.ready_to_apply || isSending || isApplying) {
            return;
        }

        setError("");
        setIsApplying(true);
        try {
            const result = await applyTaskCreation(pendingProposal);
            const { task, created_events: createdEvents } = result;
            setMessages((currentMessages) => [
                ...currentMessages,
                createMessage(
                    "assistant",
                    `Task created and scheduled: ${task.title} ` +
                        `(${task.estimated_time} minutes across ` +
                        `${createdEvents.length} calendar ` +
                        `${createdEvents.length === 1 ? "block" : "blocks"}).`
                ),
            ]);
            setPendingProposal(null);
            setMode("chat");
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsApplying(false);
        }
    }

    function cancelTask() {
        if (isSending || isApplying) {
            return;
        }

        setPendingProposal(null);
        setError("");
    }

    const value = {
        cancelTask,
        confirmTask,
        error,
        isApplying,
        isSending,
        messages,
        mode,
        pendingProposal,
        setMode,
        submitMessage,
    };

    return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}


export default ChatProvider;
