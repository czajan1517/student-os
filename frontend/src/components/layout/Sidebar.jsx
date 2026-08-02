import Navigationitem from "../layout/Navigationitem";
import {
    LayoutDashboard,
    MessageSquare,
    Calendar,
    CheckSquare,
    Settings
} from "lucide-react";

function Sidebar({activePage, setActivePage}) {


    return (
        <div className="h-full flex flex-col bg-[#EEE8E2] p-6">

            <h1 className="mb-12 text-3xl font-bold">
                StudentOS
            </h1>

            <nav className="flex-1 flex flex-col gap-13">

                <Navigationitem
                    isActive={activePage === "Dashboard"}
                    onClick={() => setActivePage("Dashboard")}
                    icon={<LayoutDashboard size={20} />}
                >
                    Dashboard
                </Navigationitem>

                <Navigationitem
                    isActive={activePage === "Chat"}
                    onClick={() => setActivePage("Chat")}
                    icon={<MessageSquare size={20} />}
                >
                    Chat
                </Navigationitem>

                <Navigationitem
                    isActive={activePage === "Calendar"}
                    onClick={() => setActivePage("Calendar")}
                    icon={<Calendar size={20} />}
                >
                    Calendar
                </Navigationitem>

                <Navigationitem
                    isActive={activePage === "Tasks"}
                    onClick={() => setActivePage("Tasks")}
                    icon={<CheckSquare size={20} />}
                >
                    Tasks
                </Navigationitem>

                <Navigationitem
                    isActive={activePage === "Settings"}
                    onClick={() => setActivePage("Settings")}
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