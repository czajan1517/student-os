from fastapi import APIRouter, HTTPException
from backend.services.task_service import TaskService
from backend.schemas.task import TaskCreate, TaskUpdate

router = APIRouter()
task_service = TaskService()


@router.post("/tasks")
def create_task(task: TaskCreate):
    return task_service.create_task(task)


@router.get("/tasks")
def get_tasks():
    return task_service.get_tasks()


@router.get("/tasks/{task_id}")
def get_task(task_id: int):
    result = task_service.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    result = task_service.update_task(task_id, task_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    result = task_service.delete_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}