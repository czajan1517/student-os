import logging

from backend.database.database import SessionLocal
from backend.database.models import CalendarEvent, Task
from backend.schemas.calendar import CalendarCreate, CalendarUpdate


logger = logging.getLogger("studentos.calendar")


class CalendarEventService:

    def create_event(self, calendar_event: CalendarCreate):
        db = SessionLocal()
        try:
            if (
                calendar_event.task_id is not None
                and db.get(Task, calendar_event.task_id) is None
            ):
                raise ValueError("Linked task was not found")

            new_event = CalendarEvent(
                title=calendar_event.title,
                description=calendar_event.description,
                priority=int(calendar_event.priority),
                task_id=calendar_event.task_id,
                locked=calendar_event.locked,
                buffer_after_minutes=calendar_event.buffer_after_minutes,
                start_date=calendar_event.start_date,
                end_date=calendar_event.end_date,
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            logger.info(
                "calendar_event_created event_id=%s task_id=%s locked=%s",
                new_event.id,
                new_event.task_id,
                new_event.locked,
            )
        except ValueError as error:
            db.rollback()
            logger.warning(
                "calendar_event_create_rejected task_id=%s reason=%s",
                calendar_event.task_id,
                type(error).__name__,
            )
            raise
        except Exception:
            db.rollback()
            logger.exception(
                "calendar_event_create_failed task_id=%s locked=%s",
                calendar_event.task_id,
                calendar_event.locked,
            )
            raise
        finally:
            db.close()


        return new_event

    def get_events(self):  ### all events
        db = SessionLocal()
        try:
            calendarevents = db.query(CalendarEvent).all()
            return calendarevents
    
        finally:
            db.close()

    def get_event(self, calendar_event_id: int):   ### one event
        db = SessionLocal()
        try: 
            one_event= db.query(CalendarEvent).filter(CalendarEvent.id == calendar_event_id).first()
            return one_event
        
        finally:

            db.close()



    def update_event(self, calendar_event_id: int, calendar_event_data: CalendarUpdate):
        db = SessionLocal()
        
        
        try:
            existing_event = db.query(CalendarEvent).filter(CalendarEvent.id == calendar_event_id).first()
            if existing_event is None:
                logger.warning(
                    "calendar_event_update_not_found event_id=%s",
                    calendar_event_id,
                )
                return None
            
            updated_data = calendar_event_data.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

            updated_start = updated_data.get(
                "start_date",
                existing_event.start_date,
            )
            updated_end = updated_data.get(
                "end_date",
                existing_event.end_date,
            )

            if updated_end <= updated_start:
                raise ValueError("End date must be later than the start date")

            if "priority" in updated_data:
                updated_data["priority"] = int(updated_data["priority"])

            if "task_id" in calendar_event_data.model_fields_set:
                task_id = calendar_event_data.task_id
                if task_id is not None and db.get(Task, task_id) is None:
                    raise ValueError("Linked task was not found")
                updated_data["task_id"] = task_id

            
            for key, value in updated_data.items():
                setattr(existing_event, key, value)

            db.commit()
            db.refresh(existing_event)
            logger.info(
                "calendar_event_updated event_id=%s changed_fields=%s",
                calendar_event_id,
                ",".join(sorted(updated_data)) or "none",
            )

        except ValueError as error:
            db.rollback()
            logger.warning(
                "calendar_event_update_rejected event_id=%s reason=%s",
                calendar_event_id,
                type(error).__name__,
            )
            raise
        except Exception:
            db.rollback()
            logger.exception(
                "calendar_event_update_failed event_id=%s",
                calendar_event_id,
            )
            raise
        finally: 
            db.close()

        return existing_event

    def delete_event(self, calendar_event_id:int):
        db = SessionLocal()

        try:

            todel_event = db.get(CalendarEvent, calendar_event_id)
            if todel_event is None:
                logger.warning(
                    "calendar_event_delete_not_found event_id=%s",
                    calendar_event_id,
                )
                return None
            
            db.delete(todel_event)
            db.commit()
            logger.info(
                "calendar_event_deleted event_id=%s",
                calendar_event_id,
            )
    
        except Exception:
            db.rollback()
            logger.exception(
                "calendar_event_delete_failed event_id=%s",
                calendar_event_id,
            )
            raise
        
        finally:
            db.close()
        return todel_event
