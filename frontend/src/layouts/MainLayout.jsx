import { useState } from "react";
import Sidebar from "../components/layout/Sidebar";
import { Outlet } from "react-router-dom";


function MainLayout() {

    return(
        <div className="flex flex-row h-screen font-inter">
            <div className="w-[20%]">
            <Sidebar />
            </div>
            <main className="flex-1 bg-[#F8F5F2] p-4">  
                <div className="flex items-center mb-4">
                    <Outlet />
                </div>
            </main>
        </div>   

    )
}

export default MainLayout;