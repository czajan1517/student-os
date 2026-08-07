import { getTasks } from "./taskApi";
import { getCalendarEvents } from "./calendarApi";

export async function getDashboardData() {
    const tasks = await getTasks();
    const events = await getCalendarEvents();

    return {
        tasks,
        events
    };
}