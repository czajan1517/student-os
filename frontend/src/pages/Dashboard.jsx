import { Sun } from "lucide-react";
import { Bell } from "lucide-react";

function Dashboard() {



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

            <div className="h-45 bg-[#FFFFFF] rounded-xl">
                Task Today
            </div>

            <div className="h-45 bg-[#FFFFFF] rounded-xl">
                Events Today

            </div>

            <div className="h-45 bg-[#FFFFFF] rounded-xl">
                Focus Time

            </div>

            <div className="h-45 bg-[#FFFFFF] rounded-xl">
                Progress 

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