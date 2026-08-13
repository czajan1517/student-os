
import { getTasks } from "./taskApi";
import { getCalendarEvents } from "./calendarApi";

export async function getDashboardData() {
    // 
    const tasks = await getTasks();
    const events = await getCalendarEvents();

    // tasks 
    const todayTasks = getTodayTasks(tasks);
    const completedTodayTasks = getCompletedtasks(todayTasks);

    // events
    const todayEvents = getTodayEvents(events);
    const nextEvent = getUpcomingEvent(todayEvents);

    return {
        tasks,
        events,
        todayTasks,
        completedTodayTasks,
        todayEvents, 
        nextEvent
    };
}


function getTodayTasks(tasks) {
    const today = new Date();

    return tasks.filter((task) => {
        if (!task.due_date){
            return false; 
        }
        const dueDate = new Date(task.due_date);


        return(
            dueDate.getFullYear() === today.getFullYear() &&
            dueDate.getMonth() === today.getMonth() &&
            dueDate.getDate() === today.getDate() 
        );
    });
}


function getCompletedtasks(tasks){
    return tasks.filter((tasks) => tasks.completed);
}


function getTodayEvents(events) {
    const today = new Date(); 

    return events.filter((event) => {
        const startDate = new Date(event.start_date)

        return( 
            startDate.getFullYear() === today.getFullYear() &&
            startDate.getMonth() === today.getMonth() &&
            startDate.getDate() === today.getDate() 
        );
    });

}

function getUpcomingEvent(events) {
    const now = new Date();

    const upcomingEvents = events.filter((event) => {
        const endDate = new Date(event.end_date);

        return endDate > now;
    });

    upcomingEvents.sort((a, b) => {
        return new Date(a.start_date) - new Date(b.start_date);
    });

    return upcomingEvents[0] ?? null;
}