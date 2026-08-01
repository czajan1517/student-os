import { useState } from "react";
import Button from "../common/Button";

function Sidebar() {

    const [active, setActive] = useState("Dashboard");

    return (
        <div className="h-full flex flex-col bg-[#EEE8E2] p-6">

            <h1 className="mb-12 text-3xl font-bold">
                StudentOS
            </h1>

            <nav className="flex-1 flex flex-col gap-4">

                <Button
                    isActive={active === "Dashboard"}
                    onClick={() => setActive("Dashboard")}
                >
                    Dashboard
                </Button>

                <Button
                    isActive={active === "Chat"}
                    onClick={() => setActive("Chat")}
                >
                    Chat
                </Button>

                <Button
                    isActive={active === "Calendar"}
                    onClick={() => setActive("Calendar")}
                >
                    Calendar
                </Button>

                <Button
                    isActive={active === "Tasks"}
                    onClick={() => setActive("Tasks")}
                >
                    Tasks
                </Button>

                <Button
                    isActive={active === "Settings"}
                    onClick={() => setActive("Settings")}
                >
                    Settings
                </Button>

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