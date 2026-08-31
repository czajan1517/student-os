import { ArrowRight, ClipboardCheck, ListTodo } from "lucide-react";
import Card from "../common/Card";
import TaskItem from "./TaskItem";
import { NavLink } from "react-router-dom";



function TaskPanel({
    tasks,
    onToggleTask,
    title = "Today's Tasks",
    description,
    showViewLink = true,
    emptyDescription = "No task scheduled for today.",
}) {

    const sortedTasks = [...tasks].sort((a, b) => {
    
    if (a.completed !== b.completed) {
        return a.completed ? 1 : -1;
    }

    if (!a.due_date && !b.due_date) {
        return new Date(b.created_at) - new Date(a.created_at);
    }

    if (!a.due_date) {
        return 1;
    }

    if (!b.due_date) {
        return -1;
    }

    return new Date(a.due_date) - new Date(b.due_date);
    });

    return (
        <Card className="overflow-hidden border border-[#EEE7E1] p-0! shadow-[0_2px_10px_rgba(77,50,32,0.05)]">
            <div className="flex flex-col w-full">

                {/* Header */}
                <div className="flex items-center justify-between border-b border-[#EEE7E1] px-6 py-4">
                    <div className="flex items-center gap-3">
                        <span className="flex size-10 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                            <ListTodo size={21} strokeWidth={1.8} />
                        </span>

                        <div>
                            <h2 className="text-xl font-semibold text-[#241C17]">
                                {title}
                            </h2>
                            <p className="text-sm text-[#7C7068]">
                                {description ?? (tasks.length
                                    ? `${tasks.length} ${tasks.length === 1 ? "task" : "tasks"} today`
                                    : "Your task list is clear")}
                            </p>
                        </div>
                    </div>

                    {showViewLink && (
                        <NavLink
                            to="/tasks"
                            className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-[#C7651E] transition-colors hover:bg-[#FFF0E5] hover:text-[#9E4812] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#C7651E]"
                        >
                            View tasks
                            <ArrowRight size={16} aria-hidden="true" />
                        </NavLink>
                    )}
                </div>

                {/* Tasks */}
                {tasks.length === 0 ? (
                    <div className="flex flex-col items-center justify-center flex-1 py-16 text-center">

                        <ClipboardCheck
                        size={28}
                        strokeWidth={1.8}
                        className="text-[#D66A1F] mb-3"
                        />
                        <p className="text-lg font-semibold">
                            You're all caught up!
                        </p>

                        <p className="text-lg text-gray-500 mt-1">
                            {emptyDescription}
                        </p>
                    </div>
                ) : (
                    <div>
                        {sortedTasks.map((task) => (
                            <TaskItem
                                key={task.id}
                                task={task}
                                onToggle={onToggleTask}
                            />
                        ))}
                    </div>
                )}
            </div>
        </Card>
    );
}

export default TaskPanel;
