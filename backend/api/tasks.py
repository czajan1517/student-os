from fastapi import APIRouter
from backend.services.task_service import TaskService
from backend.schemas.task import TaskCreate

router = APIRouter()
task_service = TaskService()


@router.post("/tasks")
def create_task(task: TaskCreate):
    return task_service.create_task(task)