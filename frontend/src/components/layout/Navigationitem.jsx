import { NavLink } from "react-router-dom";


function Navigationitem({
    icon,
    children,
    onClick,
    isActive = false,
    to
}) {
    return (
        <NavLink
            to={to}
            end={to === "/"}
            onClick={onClick}
            className={({ isActive }) =>
                `flex flex-row w-full rounded-md px-4 py-2 gap-5 transition
                ${
                    isActive
                        ? "bg-[#E8C9A8] text-[#A85A24]"
                        : "text-[#5C5248] hover:bg-[#F2DFCA] hover:text-[#A85A24]"
                }`
            }
        >
            {icon}
            <span>{children}</span>
        </NavLink>
    );
}

export default Navigationitem;