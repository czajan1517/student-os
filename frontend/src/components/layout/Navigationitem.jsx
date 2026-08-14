import { NavLink } from "react-router-dom";

function Navigationitem({ icon, children, onClick, to }) {
    return (
        <NavLink
            to={to}
            end={to === "/"}
            onClick={onClick}
            className={({ isActive }) =>
                `group flex min-h-13 w-full items-center gap-4 rounded-xl px-4 py-3 text-base font-medium transition-colors duration-150 ${
                    isActive
                        ? "bg-[#FFF0E5] text-[#B85E1B]"
                        : "text-[#30251F] hover:bg-[#FAF1E9] hover:text-[#B85E1B]"
                }`
            }
        >
            <span className="flex size-6 shrink-0 items-center justify-center">
                {icon}
            </span>
            <span>{children}</span>
        </NavLink>
    );
}

export default Navigationitem;
