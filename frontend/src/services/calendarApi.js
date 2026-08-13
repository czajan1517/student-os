const API_URL = import.meta.env.VITE_API_URL;

export async function getCalendarEvents() {
    const response = await fetch(`${API_URL}/calendar_events`);

    if (!response.ok) {
        throw new Error("Failed to fetch calendar events");
    }

    return response.json();
}