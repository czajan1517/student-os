import { useState } from "react";
import Navigationitem from "../layout/Navigationitem";
import {
    LayoutDashboard,
    MessageSquare,
    Calendar,
    CheckSquare,
    Settings
} from "lucide-react";

function Sidebar() {

    const [active, setActive] = useState("Dashboard");

    return (
        <div className="h-full flex flex-col bg-[#EEE8E2] p-6">

            <h1 className="mb-12 text-3xl font-bold">
                StudentOS
            </h1>

            <nav className="flex-1 flex flex-col gap-13">

                <Navigationitem
                    isActive={active === "Dashboard"}
                    onClick={() => setActive("Dashboard")}
                    icon={<LayoutDashboard size={20} />}
                >
                    Dashboard
                </Navigationitem>

                <Navigationitem
                    isActive={active === "Chat"}
                    onClick={() => setActive("Chat")}
                    icon={<MessageSquare size={20} />}
                >
                    Chat
                </Navigationitem>

                <Navigationitem
                    isActive={active === "Calendar"}
                    onClick={() => setActive("Calendar")}
                    icon={<Calendar size={20} />}
                >
                    Calendar
                </Navigationitem>

                <Navigationitem
                    isActive={active === "Tasks"}
                    onClick={() => setActive("Tasks")}
                    icon={<CheckSquare size={20} />}
                >
                    Tasks
                </Navigationitem>

                <Navigationitem
                    isActive={active === "Settings"}
                    onClick={() => setActive("Settings")}
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