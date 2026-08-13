const API_URL = import.meta.env.VITE_API_URL;

export async function getTasks() {
    const response = await fetch(`${API_URL}/tasks`);

    if (!response.ok) {
        throw new Error("Failed to fetch tasks");
    }

    return response.json();
}


export async function updateTask(id, taskData) {
    const response = await fetch(`${API_URL}/tasks/${id}`, {
    method: "PUT",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify(taskData),
    });

    if (!response.ok) {
        throw new Error("Failed to update tasks");
    }

    return response.json();
}