const API_URL = import.meta.env.VITE_API_URL;

function getErrorMessage(payload) {
    if (typeof payload?.detail === "string") {
        return payload.detail;
    }

    if (Array.isArray(payload?.detail)) {
        return payload.detail
            .map((error) => error.msg)
            .filter(Boolean)
            .join("; ");
    }

    return "StudentOS AI could not respond. Please try again.";
}

async function postAI(path, body) {
    const response = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(getErrorMessage(payload));
    }

    return payload;
}

export function sendChatMessage(messages) {
    return postAI("/ai/respond", { messages });
}

export function previewTaskCreation(message) {
    return postAI("/ai/actions/tasks/preview", { message });
}

export function applyTaskCreation(proposal) {
    return postAI("/ai/actions/tasks/apply", {
        proposal,
        confirmed: true,
    });
}
