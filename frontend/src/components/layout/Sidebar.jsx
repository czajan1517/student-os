import Navigationitem from "../layout/Navigationitem";
import {
    LayoutDashboard,
    MessageSquare,
    Calendar,
    CheckSquare,
    Settings
} from "lucide-react";

function Sidebar() {


    return (
        <div className="h-full flex flex-col bg-[#EEE8E2] p-6">

            <h1 className="mb-12 text-3xl font-bold">
                StudentOS
            </h1>

            <nav className="flex-1 flex flex-col gap-13">

                <Navigationitem
                    to="/"
                    icon={<LayoutDashboard size={20} />}
                >
                    Dashboard
                </Navigationitem>

                <Navigationitem
                    to="/chat"
                    icon={<MessageSquare size={20} />}
                >
                    Chat
                </Navigationitem>

                <Navigationitem
                    to="/calendar"
                    icon={<Calendar size={20} />}
                >
                    Calendar
                </Navigationitem>

                <Navigationitem
                    to="/tasks"
                    icon={<CheckSquare size={20} />}
                >
                    Tasks
                </Navigationitem>

                <Navigationitem
                    to="/settings"
                    icon={<Settings size={20} />}
                >
                    Settings
                </Navigationitem>

            </nav>

            <div>
                <p className="text-xl">
                    Profile
                </p>
            </div>

        </div>
    );
}

export default Sidebar;