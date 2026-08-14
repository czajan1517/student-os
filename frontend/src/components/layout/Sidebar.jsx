import Navigationitem from "./Navigationitem";
import {
    CalendarDays,
    ChevronRight,
    House,
    MessageCircle,
    Settings,
    SquareCheckBig,
    UserRound,
} from "lucide-react";

const iconProps = {
    size: 22,
    strokeWidth: 1.8,
};

function Sidebar() {
    return (
        <aside className="flex h-full min-h-screen flex-col border-r border-[#EEE7E1] bg-[#FFFDFC] px-5 py-8 text-[#241C17]">
            <div className="flex items-center gap-4 px-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-linear-to-br from-[#D97825] to-[#75300F] shadow-[0_4px_10px_rgba(117,48,15,0.22)]">
                    <span className="font-serif text-2xl font-bold italic leading-none text-white">
                        S
                    </span>
                </div>
                <span className="text-2xl font-semibold tracking-[-0.025em]">
                    StudentOS
                </span>
            </div>

            <nav aria-label="Main navigation" className="mt-14 flex flex-col gap-2">
                <Navigationitem
                    to="/"
                    icon={<House {...iconProps} />}
                >
                    Today
                </Navigationitem>

                <Navigationitem
                    to="/chat"
                    icon={<MessageCircle {...iconProps} />}
                >
                    Chat
                </Navigationitem>

                <Navigationitem
                    to="/calendar"
                    icon={<CalendarDays {...iconProps} />}
                >
                    Calendar
                </Navigationitem>

                <Navigationitem
                    to="/tasks"
                    icon={<SquareCheckBig {...iconProps} />}
                >
                    Tasks
                </Navigationitem>

                <div className="my-3 border-t border-[#E9E1DB]" />

                <Navigationitem
                    to="/settings"
                    icon={<Settings {...iconProps} />}
                >
                    Settings
                </Navigationitem>
            </nav>

            <button
                type="button"
                className="mt-auto flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-[#FAF1E9]"
                aria-label="View Jan Dhave's profile"
            >
                <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#F2DDC8] text-[#9A5A2B]">
                    <UserRound size={27} strokeWidth={1.6} />
                </span>

                <span className="min-w-0 flex-1">
                    <span className="block truncate text-base font-semibold">
                        Jan Dhave
                    </span>
                    <span className="mt-0.5 block text-sm text-[#6E625A]">
                        View Profile
                    </span>
                </span>

                <ChevronRight size={20} strokeWidth={1.8} />
            </button>
        </aside>
    );
}

export default Sidebar;
