import Sidebar from "../components/layout/Sidebar";
import { Outlet } from "react-router-dom";

function MainLayout() {
    return (
        <div className="flex min-h-screen bg-[#F8F5F2] font-sans text-[#241C17]">
            <div className="sticky top-0 h-screen w-72 shrink-0">
                <Sidebar />
            </div>

            <main className="min-w-0 flex-1 bg-[#F8F5F2] px-10 py-8">
                <Outlet />
            </main>
        </div>
    );
}

export default MainLayout;
