import { Bell, Calendar, CheckSquare, Clock3, Sun, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import StatisticsCard from "../components/dashboard/StatisticsCard";
import TaskPanel from "../components/dashboard/TaskPanel";
import Schedulepanel from "../components/dashboard/Schedulepanel";
import { getDashboardData } from "../services/dashboardApi";
import { updateTask } from "../services/taskApi";

function Dashboard() {
    const [todayTasks, setTodayTasks] = useState([]);
    const [todayEvents, setTodayEvents] = useState([]);
    const [nextEvent, setNextEvent] = useState(null);

    const completedTodayTasks = todayTasks.filter((task) => task.completed);
    const taskProgress = todayTasks.length
        ? (completedTodayTasks.length / todayTasks.length) * 100
        : 0;

    async function handleToggleTask(task) {
        const updatedTask = await updateTask(task.id, {
            completed: !task.completed,
        });

        setTodayTasks((currentTasks) =>
            currentTasks.map((currentTask) =>
                currentTask.id === updatedTask.id ? updatedTask : currentTask
            )
        );
    }

    useEffect(() => {
        async function loadDashboardData() {
            const data = await getDashboardData();

            setTodayTasks(data.todayTasks);
            setTodayEvents(data.todayEvents);
            setNextEvent(data.nextEvent);
        }

        loadDashboardData();
    }, []);

    const nextEventTime = nextEvent
        ? new Date(nextEvent.start_date).toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
          })
        : null;
    const nextEventTitle = nextEvent?.title ?? nextEvent?.name;

    return (
        <div className="w-full">
            {/* Greetings */}
            <div className="flex flex-row items-start justify-between px-4 text-4xl font-bold">
                <div className="flex flex-row">
                    Good morning, User
                    <Sun
                        size={30}
                        className="inline-block align-middle text-[#A85A24]"
                    />
                </div>

                <div className="flex flex-row gap-4 pr-4 text-2xl font-bold">
                    <Bell size={20} /> date calendar and notif
                </div>
            </div>

            {/* Dashboard statistics */}
            <div className="mt-9 grid grid-cols-1 gap-5 md:grid-cols-2 2xl:grid-cols-4">
                <StatisticsCard
                    icon={<CheckSquare size={24} strokeWidth={1.8} />}
                    title="Tasks Today"
                    value={todayTasks.length}
                    subtitle={`${completedTodayTasks.length} completed`}
                    subtitleClassName="text-[#6E625A]"
                    progress={taskProgress}
                />

                <StatisticsCard
                    icon={<Calendar size={24} strokeWidth={1.8} />}
                    title="Events Today"
                    value={todayEvents.length}
                    subtitle={
                        nextEvent ? (
                            <>
                                <span className="font-medium text-[#B85E1B]">Next:</span>{" "}
                                <span className="text-[#4E433C]">
                                    {nextEventTime}
                                    {nextEventTitle ? ` – ${nextEventTitle}` : ""}
                                </span>
                            </>
                        ) : (
                            "No upcoming events"
                        )
                    }
                />

                <StatisticsCard
                    icon={<Clock3 size={24} strokeWidth={1.8} />}
                    title="Focus Time"
                    value="5h 30m"
                    subtitle="Keep it up!"
                />

                <StatisticsCard
                    icon={<TrendingUp size={24} strokeWidth={1.8} />}
                    title="Progress"
                    value="72%"
                    subtitle="This week"
                />
            </div>

            <div className="mt-8 grid grid-cols-1 gap-9 xl:grid-cols-2">
                {/* Task Panel */}
                <TaskPanel tasks={todayTasks} onToggleTask={handleToggleTask} />

                {/* Today's Schedule */}
                <Schedulepanel events={todayEvents} nextEvent={nextEvent} />
            </div>

            {/* Quote */}
            <div className="mt-16 grid grid-cols-1">
                <div className="h-28 rounded-xl bg-white">Quote</div>
            </div>
        </div>
    );
}

export default Dashboard;
