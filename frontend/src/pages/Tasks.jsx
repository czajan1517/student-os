import { useEffect, useState } from "react";
import TaskPanel from "../components/dashboard/TaskPanel";
import { getTasks, updateTask } from "../services/taskApi";


function Tasks() {
    const [tasks, setTasks] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function loadTasks() {
            try {
                setTasks(await getTasks());
            } catch (requestError) {
                setError(requestError.message);
            } finally {
                setIsLoading(false);
            }
        }

        loadTasks();
    }, []);

    async function handleToggleTask(task) {
        try {
            const updatedTask = await updateTask(task.id, {
                completed: !task.completed,
            });

            setTasks((currentTasks) =>
                currentTasks.map((currentTask) =>
                    currentTask.id === updatedTask.id
                        ? updatedTask
                        : currentTask
                )
            );
        } catch (requestError) {
            setError(requestError.message);
        }
    }

    return (
        <section className="mx-auto max-w-5xl">
            <div className="mb-7">
                <h1 className="text-3xl font-semibold tracking-tight text-[#241C17]">
                    Tasks
                </h1>
                <p className="mt-2 text-sm text-[#756960]">
                    Review every task, including tasks without a due date.
                </p>
            </div>

            {error && (
                <p
                    className="mb-4 rounded-xl border border-[#F3C7B0] bg-[#FFF2EB] px-4 py-3 text-sm text-[#A84E18]"
                    role="alert"
                >
                    {error}
                </p>
            )}

            {isLoading ? (
                <p className="rounded-2xl border border-[#EEE7E1] bg-white px-6 py-10 text-center text-[#756960]">
                    Loading tasks…
                </p>
            ) : (
                <TaskPanel
                    tasks={tasks}
                    onToggleTask={handleToggleTask}
                    title="All Tasks"
                    description={`${tasks.length} ${tasks.length === 1 ? "task" : "tasks"}`}
                    showViewLink={false}
                    emptyDescription="No tasks have been created yet."
                />
            )}
        </section>
    );
}

export default Tasks;
