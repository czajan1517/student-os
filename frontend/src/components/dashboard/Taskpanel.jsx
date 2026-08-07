import Card from "../common/Card";

function TaskPanel({ tasks }) {
    return (
        <Card>
            <h2>Today's Tasks</h2>

            {tasks.map((task) => (
                <div key={task.id}>
                    {task.title}
                </div>
            ))}
        </Card>
    );
}

export default TaskPanel;