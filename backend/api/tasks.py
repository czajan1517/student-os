from fastapi import APIRouter
from backend.services.task_service import TaskService

router = APIRouter()
task_service = TaskService()