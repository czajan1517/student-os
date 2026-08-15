from backend.database.database import SessionLocal
from backend.database.models import CalendarEvent
from backend.schemas.calendar import CalendarCreate, CalendarUpdate


class CalendarEventService: 

    def create_event(self, calendar_event: CalendarCreate):
        db = SessionLocal()
        new_event = CalendarEvent(
            title=calendar_event.title,
            description=calendar_event.description,
            priority=int(calendar_event.priority),
            start_date=calendar_event.start_date,
            end_date=calendar_event.end_date
        )
        try:
            db.add(new_event)
            db.commit()
            db.refresh(new_event)    
        except Exception:
            db.rollback()
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

            
            for key, value in updated_data.items():
                setattr(existing_event, key, value)

            db.commit()
            db.refresh(existing_event)

        except Exception:
            db.rollback()
            raise
        finally: 
            db.close()

        return existing_event

    def delete_event(self, calendar_event_id:int):
        db = SessionLocal()

        try:

            todel_event = db.get(CalendarEvent, calendar_event_id)
            if todel_event is None:
                return None
            
            db.delete(todel_event)
            db.commit()
    
        except Exception:
            db.rollback()
            raise
        
        finally:
            db.close()
        return todel_event
