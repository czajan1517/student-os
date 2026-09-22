
function formatPriority(priority) {
    if (priority === 1) {
        return "High";
    }

    if (priority === 2) {
        return "Medium";
    }

    if (priority === 3) {
        return "Low";
    }

    return "Normal";
}

function formatDateTime(date) {
    if (!date) {
        return "";
    }

    return new Date(date).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });
}

function formatSchedule(startDate, endDate) {
    if (!startDate || !endDate) {
        return "";
    }

    const start = new Date(startDate);
    const end = new Date(endDate);
    const sameDay = start.toDateString() === end.toDateString();
    const startLabel = start.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });
    const endLabel = end.toLocaleString([], sameDay
        ? { hour: "numeric", minute: "2-digit" }
        : {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
        });

    return `${startLabel}–${endLabel}`;
}

function TaskItem({ task, onToggle }) {
    const scheduleLabel = formatSchedule(
        task.next_scheduled_start,
        task.next_scheduled_end
    );
    const dueLabel = formatDateTime(task.due_date);

    return (
        <div className={`flex items-center justify-between px-3 py-4 border-b border-gray-200 ${
        task.completed ? "bg-gray-50 opacity-60" : "bg-white"
        }`}
        >            

            <div className="flex items-center gap-4">
            
                {/* Checkbox */}
                    <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => onToggle(task)}
                    className="w-7 h-7 accent-[#A85A24] cursor-pointer"
                    /> 
                {/* Task */}
            <div>
                    <p
                        className={`font-semibold ${
                            task.completed ? "line-through text-gray-500" : ""
                        }`}
                    >
                        {task.title}
                    </p>

                    <p className="text-sm text-gray-500">
                       {task.description}
                    </p>

                </div>
            </div>


                {/* Priority, scheduled time, and deadline */}
            <div className="text-right shrink-0">
                <p className="text-sm font-medium text-[#A85A24]">
                    {formatPriority(task.priority)}
                </p>

                {scheduleLabel && (
                    <p className="text-sm text-gray-500">
                        Scheduled {scheduleLabel}
                    </p>
                )}

                {dueLabel && (
                    <p className="text-xs text-gray-400">
                        Due {dueLabel}
                    </p>
                )}
            </div>


        </div>
    );
}

export default TaskItem;
