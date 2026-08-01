function Button({
    children,
    onClick,
    isActive = false
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`w-full rounded-md px-4 py-2 text-left transition
            ${
                isActive
                    ? "bg-[#C97A40] text-white"
                    : "text-gray-800 hover:bg-[#D99561] hover:text-white"
            }`}
        >
            {children}
        </button>
    );
}

export default Button;