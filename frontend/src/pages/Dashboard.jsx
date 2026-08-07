import { Calendar, Sun } from "lucide-react";
import { Bell } from "lucide-react";
import StatisticsCard from "../components/dashboard/StatisticsCard";
import { CheckSquare, Clock3, TrendingUp } from "lucide-react";
// ------ 
import { useEffect, useState } from "react";
import { getDashboardData } from "../services/dashboardApi";


function Dashboard() {

    const [tasks, setTasks] = useState([]);
    const [events, setEvents] = useState([]);

    useEffect(() => {
        async function loadDashboardData() {
            const data = await getDashboardData();

            setTasks(data.tasks);
            setEvents(data.events);
        }

        loadDashboardData();
    }, []);


    return (
    <div>    


        <div className="flex flex-row text-4xl font-bold pl-4 gap-210">
           <div className="text-left">
            Good morning, <Sun size={30} className="text-[#A85A24] inline-block align-middle" />
            </div>  
       

            <div className="flex flex-row text-2xl font-bold pr-4 gap-4">
               <Bell size={20} /> date calendar and notif
            </div>

        </div>


        <div className="flex-1 grid grid-cols-4 gap-9 mt-9">

            <div>

                <StatisticsCard
                    icon={<CheckSquare size={24} />}
                    title="Tasks Today"
                    value={tasks.length}
                    subtitle="3 completed"
                />

            </div>

            <div>
                <StatisticsCard
                    icon={<Calendar size={24} />}
                    title="Events Today"
                    value={events.length}
                    subtitle="Next: 2:00 PM"
                />
            </div>

            <div>
                <StatisticsCard
                    icon={<Clock3 size={24} />}
                    title="Focus Time"
                    value="5h 30m"
                    subtitle="Keep it up!"
                />

            </div>

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
            <div className="h-96 bg-white rounded-xl">


                Today's Task


            </div>

            <div className="h-96 bg-white rounded-xl">


                Today's Schedule

                
            </div>
        </div>


        <div className="flex grid grid-cols-1 mt-16">

            <div className="h-28 bg-white rounded-xl">
                Quote
            </div>

        </div>





    </div>

    )
}

export default Dashboard;