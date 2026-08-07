
// TODO: change the url after backend deployment
const API_URL = "http://127.0.0.1:8000";

export async function getCalendarEvents() {
    const response = await fetch(`${API_URL}/calendar_events`);

    if (!response.ok) {
        throw new Error("Failed to fetch calendar events");
    }

    return response.json();
}