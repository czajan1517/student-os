import { useState } from "react";
import Sidebar from "../components/layout/Sidebar";



function MainLayout() {
    const [activePage, setActivePage] = useState("Dashboard")

    return(
        <div className="flex flex-row h-screen font-inter">
            <div className="w-[20%]">
            <Sidebar
                activePage={activePage}
                setActivePage={setActivePage}
             />
            </div>
            <main className="flex-1 bg-[#F8F5F2] p-4">  
                <div className="flex items-center mb-4">
                    Main Content - {activePage}
                </div>
            </main>
        </div>   

    )
}

export default MainLayout;