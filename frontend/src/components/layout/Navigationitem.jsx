

function Navigationitem({
    icon,
    children,
    onClick,
    isActive = false
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`flex flex-row w-full rounded-md px-4 py-2 text-left transition gap-5
            ${
                isActive
                    ? "bg-[#E8C9A8] text-[#A85A24]"
                    : "text-[#5C5248] hover:bg-[#F2DFCA] hover:text-[#5C5248]"
            }`}
        >   
            {icon}
            {children}
        </button>
    );
}

export default Navigationitem;