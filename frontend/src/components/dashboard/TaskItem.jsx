
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

function formatTaskTime(date) {
    if (!date) {
        return "";
    }

    return new Date(date).toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
    });
}

function TaskItem({ task, onToggle }) {
        console.log("TaskItem received:", task);

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


                {/* Priority and Due Time */}
            <div className="text-right shrink-0">
                <p className="text-sm font-medium text-[#A85A24]">
                    {formatPriority(task.priority)}
                </p>

                <p className="text-sm text-gray-500">
                    {formatTaskTime(task.due_date)}
                </p>
            </div>


        </div>
    );
}

export default TaskItem;