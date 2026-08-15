from fastapi import APIRouter, HTTPException, status
from backend.services.task_service import TaskService
from backend.schemas.common import MessageResponse
from backend.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter()
task_service = TaskService()


@router.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(task: TaskCreate):
    return task_service.create_task(task)


@router.get("/tasks", response_model=list[TaskRead])
def get_tasks():
    return task_service.get_tasks()


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int):
    result = task_service.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_data: TaskUpdate):
    result = task_service.update_task(task_id, task_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
def delete_task(task_id: int):
    result = task_service.delete_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
