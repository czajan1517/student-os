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

export async function sendChatMessage(messages) {
    const response = await fetch(`${API_URL}/ai/respond`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages }),
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(getErrorMessage(payload));
    }

    return payload;
}
