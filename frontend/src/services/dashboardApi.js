
import { getTasks } from "./taskApi";
import { getCalendarEvents } from "./calendarApi";

export async function getDashboardData() {
    const tasks = await getTasks();
    const events = await getCalendarEvents();
    const todayTasks = getTodayTasks(tasks);
    const completedTodayTasks = getCompletedtasks(todayTasks);
    

    return {
        tasks,
        events,
        todayTasks,
        completedTodayTasks
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