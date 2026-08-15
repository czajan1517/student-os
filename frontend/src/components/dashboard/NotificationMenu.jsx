import { Bell, BellOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

function NotificationMenu({ notifications = [] }) {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);
    const unreadCount = notifications.filter(
        (notification) => !notification.read
    ).length;

    useEffect(() => {
        if (!isOpen) {
            return undefined;
        }

        function handlePointerDown(event) {
            if (!menuRef.current?.contains(event.target)) {
                setIsOpen(false);
            }
        }

        function handleKeyDown(event) {
            if (event.key === "Escape") {
                setIsOpen(false);
            }
        }

        document.addEventListener("pointerdown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("pointerdown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [isOpen]);

    return (
        <div ref={menuRef} className="relative">
            <button
                type="button"
                className="relative flex size-11 items-center justify-center rounded-full border border-[#E8DED6] bg-white text-[#4E433C] shadow-[0_2px_8px_rgba(77,50,32,0.06)] transition-colors hover:border-[#E1C3AD] hover:bg-[#FFF6EF] hover:text-[#B85E1B] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#C7651E]"
                aria-label={
                    unreadCount
                        ? `Notifications, ${unreadCount} unread`
                        : "Notifications"
                }
                aria-haspopup="true"
                aria-expanded={isOpen}
                aria-controls="dashboard-notifications"
                onClick={() => setIsOpen((current) => !current)}
            >
                <Bell size={21} strokeWidth={1.8} aria-hidden="true" />

                {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 size-2.5 rounded-full border-2 border-white bg-[#D55D20]" />
                )}
            </button>

            {isOpen && (
                <div
                    id="dashboard-notifications"
                    className="absolute top-full right-0 z-40 mt-3 w-80 overflow-hidden rounded-xl border border-[#E8DED6] bg-white shadow-[0_16px_40px_rgba(65,42,28,0.16)]"
                >
                    <div className="flex items-center justify-between border-b border-[#EEE7E1] px-5 py-4">
                        <div>
                            <h2 className="text-base font-semibold text-[#241C17]">
                                Notifications
                            </h2>
                            <p className="mt-0.5 text-xs text-[#7C7068]">
                                {unreadCount
                                    ? `${unreadCount} unread`
                                    : "You're all caught up"}
                            </p>
                        </div>
                    </div>

                    <div className="max-h-80 overflow-y-auto overscroll-contain">
                        {notifications.length === 0 ? (
                            <div className="flex flex-col items-center px-6 py-10 text-center">
                                <span className="flex size-11 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                                    <BellOff
                                        size={21}
                                        strokeWidth={1.8}
                                        aria-hidden="true"
                                    />
                                </span>
                                <p className="mt-3 text-sm font-semibold text-[#3D3028]">
                                    No new notifications
                                </p>
                                <p className="mt-1 text-xs leading-5 text-[#82766E]">
                                    Updates and reminders will appear here.
                                </p>
                            </div>
                        ) : (
                            <ul className="divide-y divide-[#F0E9E3]">
                                {notifications.map((notification) => (
                                    <li
                                        key={notification.id}
                                        className={`px-5 py-4 ${
                                            notification.read
                                                ? "bg-white"
                                                : "bg-[#FFF8F2]"
                                        }`}
                                    >
                                        <div className="flex gap-3">
                                            <span
                                                className={`mt-1.5 size-2 shrink-0 rounded-full ${
                                                    notification.read
                                                        ? "bg-[#D8D0CA]"
                                                        : "bg-[#D55D20]"
                                                }`}
                                            />
                                            <div className="min-w-0">
                                                <p className="text-sm font-semibold text-[#30251F]">
                                                    {notification.title}
                                                </p>
                                                {notification.message && (
                                                    <p className="mt-1 text-xs leading-5 text-[#6E625A]">
                                                        {notification.message}
                                                    </p>
                                                )}
                                                {notification.time && (
                                                    <p className="mt-2 text-[0.7rem] font-medium text-[#A15725]">
                                                        {notification.time}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default NotificationMenu;
