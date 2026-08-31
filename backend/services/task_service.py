import logging

from backend.database.database import SessionLocal
from backend.database.models import Task
from backend.schemas.task import TaskCreate, TaskUpdate


logger = logging.getLogger("studentos.tasks")


class TaskService:

    def create_task(self, task: TaskCreate):
        db = SessionLocal()
        new_task = Task(
            title=task.title,
            description=task.description,
            priority=int(task.priority),
            estimated_time=task.estimated_time,
            task_type=task.task_type.value,
            effort_level=int(task.effort_level),
            recovery_buffer_minutes=task.recovery_buffer_minutes,
            splittable=task.splittable,
            due_date=task.due_date,
            completed=task.completed,
        )
        try:
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            logger.info(
                "task_created task_id=%s task_type=%s priority=%s",
                new_task.id,
                new_task.task_type,
                new_task.priority,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "task_create_failed task_type=%s priority=%s",
                task.task_type.value,
                int(task.priority),
            )
            raise
        finally:
            db.close()


        return new_task

    def get_tasks(self):  ### all tasks 
        db = SessionLocal()
        try:
            tasks = db.query(Task).all()
            return tasks
    
        finally:
            db.close()

    def get_task(self, task_id: int):   ### one task
        db = SessionLocal()
        try: 
            one_task = db.query(Task).filter(Task.id == task_id).first()
            return one_task
        
        finally:

            db.close()



    def update_task(self, task_id: int, task_data: TaskUpdate):
        db = SessionLocal()
        
        
        try:
            existing_task = db.query(Task).filter(Task.id == task_id).first()
            if existing_task is None:
                logger.warning("task_update_not_found task_id=%s", task_id)
                return None
            
            updated_data = task_data.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            if "due_date" in task_data.model_fields_set:
                updated_data["due_date"] = task_data.due_date

            if "priority" in updated_data:
                updated_data["priority"] = int(updated_data["priority"])

            if "task_type" in updated_data:
                updated_data["task_type"] = updated_data["task_type"].value

            if "effort_level" in updated_data:
                updated_data["effort_level"] = int(updated_data["effort_level"])

            
            for key, value in updated_data.items():
                setattr(existing_task, key, value)

            db.commit()
            db.refresh(existing_task)
            logger.info(
                "task_updated task_id=%s changed_fields=%s",
                task_id,
                ",".join(sorted(updated_data)) or "none",
            )

        except Exception:
            db.rollback()
            logger.exception("task_update_failed task_id=%s", task_id)
            raise
        finally: 
            db.close()

        return existing_task

    def delete_task(self, task_id:int):
        db = SessionLocal()

        try:

            todel_task = db.get(Task, task_id)
            if todel_task is None:
                logger.warning("task_delete_not_found task_id=%s", task_id)
                return None
            
            db.delete(todel_task)
            db.commit()
            logger.info("task_deleted task_id=%s", task_id)
    
        except Exception:
            db.rollback()
            logger.exception("task_delete_failed task_id=%s", task_id)
            raise
        
        finally:
            db.close()
        return todel_task




        

