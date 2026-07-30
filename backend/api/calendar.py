from fastapi import APIRouter, HTTPException
from backend.services.calendar_service import CalendarEventService
from backend.schemas.calendar import CalendarCreate, CalendarUpdate

router = APIRouter()
calevent_service = CalendarEventService()


@router.post("/calendar_events")
def create_event(calendar_event: CalendarCreate):
    return calevent_service.create_event(calendar_event)


@router.get("/calendar_events")
def get_events():
    return calevent_service.get_events()


@router.get("/calendar_events/{calendar_event_id}")
def get_event(calendar_event_id: int):
    result = calevent_service.get_event(calendar_event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.put("/calendar_events/{calendar_event_id}")
def update_event(calendar_event_id: int, calendar_event_data: CalendarUpdate):
    result = calevent_service.update_event(calendar_event_id, calendar_event_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.delete("/calendar_events/{calendar_event_id}")
def delete_event(calendar_event_id: int):
    result = calevent_service.delete_event(calendar_event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

