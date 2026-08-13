import { Calendar, Sun } from "lucide-react";
import { Bell } from "lucide-react";
import StatisticsCard from "../components/dashboard/StatisticsCard";
import { CheckSquare, Clock3, TrendingUp } from "lucide-react";

// stat card data
import { useEffect, useState } from "react";
import { getDashboardData } from "../services/dashboardApi";

// task panel 
import TaskPanel from "../components/dashboard/TaskPanel";
import { updateTask } from "../services/taskApi";



function Dashboard() {

    const [tasks, setTasks] = useState([]);
    const [events, setEvents] = useState([]);
    const [todayTasks, setTodayTasks] = useState([])
    const [todayEvents, setTodayEvents] = useState([])
    const [nextEvent, setNextEvent] = useState(null);

    const completedTodayTasks = todayTasks.filter(
        (task) => task.completed
    );

    async function handleToggleTask(task) {
        const updatedTask = await updateTask(task.id, {
            completed: !task.completed
        });

        setTodayTasks((currentTasks) =>
            currentTasks.map((currentTask) =>
                currentTask.id === updatedTask.id
                    ? updatedTask
                    : currentTask
            )
        );
    }

    useEffect(() => {
        async function loadDashboardData() {
            const data = await getDashboardData();

            setTasks(data.tasks);
            setEvents(data.events);
            setTodayTasks(data.todayTasks);
            setTodayEvents(data.todayEvents);
            setNextEvent(data.nextEvent);

        }

        loadDashboardData();
    }, []);


    return (
    <div>    

        {/* Greetings */}
        <div className="flex flex-row text-4xl font-bold pl-4 gap-210">
           <div className="flex flex-row">
            Good morning, User <Sun size={30} className="text-[#A85A24] inline-block align-middle" />
            </div>  
       

            <div className="flex flex-row text-2xl font-bold pr-4 gap-4">
               <Bell size={20} /> date calendar and notif
            </div>

        </div>


        {/* Task Today statcard*/}
        <div className="flex-1 grid grid-cols-4 gap-9 mt-9">

            <div>

                <StatisticsCard
                    icon={<CheckSquare size={24} />}
                    title="Tasks Today"
                    value={todayTasks.length}
                    subtitle={`${completedTodayTasks.length} completed`}
                />

            </div>


        {/* Events Today statcard*/}
            <div>
                <StatisticsCard
                    icon={<Calendar size={24} />}
                    title="Events Today"
                    value={todayEvents.length}
                    subtitle={
                        nextEvent
                        ? `Next: ${new Date(nextEvent.start_date).toLocaleTimeString([], {
                                    hour: "numeric",
                                    minute: "2-digit"
                                })}`
                        : "No upcoming events"
                    }
                />
            </div>

                    
        {/* Focus Time statcard*/}
            <div>
                <StatisticsCard
                    icon={<Clock3 size={24} />}
                    title="Focus Time"
                    value="5h 30m"
                    subtitle="Keep it up!"
                />

            </div>


        {/* Progress statcard*/}
            <div>
               <StatisticsCard
                    icon={<TrendingUp size={24} />}
                    title="Progress"
                    value="72%"
                    subtitle="This week"
                />
            </div>
        </div>



        <div className="grid grid-cols-2 gap-9 mt-8">

        {/* Task Panel */}
            <TaskPanel 
            tasks={todayTasks} 
            onToggleTask={handleToggleTask}
            />


        {/* Today's Schedule */}
            <div className="h-96 bg-white rounded-xl">


                Today's Schedule

                
            </div>
        </div>


        {/* Qoute */}
        <div className="flex grid grid-cols-1 mt-16">

            <div className="h-28 bg-white rounded-xl">
                Quote
            </div>
        </div>
    </div>

    )
}

export default Dashboard;