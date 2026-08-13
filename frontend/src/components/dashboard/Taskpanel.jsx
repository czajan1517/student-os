import Card from "../common/Card";
import TaskItem from "./TaskItem";
import { Link } from "react-router-dom";

function TaskPanel({ tasks, onToggleTask }) {

    const sortedTasks = [...tasks].sort((a, b) => {
    
    if (a.completed !== b.completed) {
        return a.completed ? 1 : -1;
    }

    return new Date(a.due_date) - new Date(b.due_date);
    });

    return (
        <Card>
            <div className="flex flex-col w-full">

                {/* Header */}
                <div className="flex items-center justify-between px-2 py-2 border-b border-gray-200">
                    <h2 className="text-xl font-semibold">
                        Today's Tasks
                    </h2>

                    <Link
                        to="/tasks"
                        className="text-base font-medium text-[#D66A1F] hover:text-[#A85A24] transition"                    
                        >
                        View all
                    </Link>
                </div>

                {/* Tasks */}
                <div>
                    {sortedTasks.map((task) => (
                        <TaskItem
                            key={task.id}
                            task={task}
                            onToggle={onToggleTask}
                        />
                    ))}
                </div>

            </div>
        </Card>
    );
}

export default TaskPanel;