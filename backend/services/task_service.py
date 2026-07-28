from backend.database.database import SessionLocal
from backend.database.models import Task
from backend.schemas.task import TaskCreate

class TaskService: 

    def create_task(self, task: TaskCreate):
        db = SessionLocal()
        new_task = Task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            estimated_time=task.estimated_time,
            due_date=task.due_date,
        )
        try:
            db.add(new_task)
            db.commit()
            db.refresh(new_task)    
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


        return new_task

    def get_task(self):
        pass

    def update_task(self, task_id: int, task_data):
        pass

    def delete_task(self, task_id:int):
        pass

