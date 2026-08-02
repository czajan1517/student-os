from backend.database.database import SessionLocal
from backend.database.models import Task
from backend.schemas.task import TaskCreate, TaskUpdate



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
                return None
            
            updated_data = task_data.model_dump(exclude_unset=True)

            
            for key, value in updated_data.items():
                setattr(existing_task, key, value)

            db.commit()
            db.refresh(existing_task)

        except Exception:
            db.rollback()
            raise
        finally: 
            db.close()

        return existing_task

    def delete_task(self, task_id:int):
        db = SessionLocal()

        try:

            todel_task = db.get(Task, task_id)
            if todel_task is None:
                return None
            
            db.delete(todel_task)
            db.commit()
    
        except Exception:
            db.rollback()
            raise
        
        finally:
            db.close()
        return todel_task




        

