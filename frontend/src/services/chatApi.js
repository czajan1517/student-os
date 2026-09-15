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

    if (typeof payload?.detail?.message === "string") {
        return payload.detail.message;
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

function getBrowserTimezoneName() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
    } catch {
        return null;
    }
}

function getBrowserTimeContext() {
    const utcOffsetMinutes = -new Date().getTimezoneOffset();
    return {
        timezone_name: getBrowserTimezoneName(),
        utc_offset_minutes: Number.isFinite(utcOffsetMinutes)
            ? utcOffsetMinutes
            : null,
    };
}

export function sendChatMessage(messages) {
    return postAI("/ai/respond", { messages });
}

export function previewTaskCreation(message, currentProposal = null) {
    const pendingClarification =
        currentProposal?.pending_clarifications?.[0] ?? null;

    return postAI("/ai/actions/tasks/preview", {
        message,
        current_proposal: currentProposal,
        answering_field: pendingClarification?.field ?? null,
        latest_answer: pendingClarification ? message : null,
        ...getBrowserTimeContext(),
    });
}

export function applyTaskCreation(proposal) {
    return postAI("/ai/actions/tasks/apply", {
        proposal,
        confirmed: true,
    });
}
