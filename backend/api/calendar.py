from fastapi import APIRouter, HTTPException, status
from backend.services.calendar_service import CalendarEventService
from backend.schemas.calendar import CalendarCreate, CalendarRead, CalendarUpdate
from backend.schemas.common import MessageResponse

router = APIRouter()
calevent_service = CalendarEventService()


@router.post(
    "/calendar_events",
    response_model=CalendarRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(calendar_event: CalendarCreate):
    return calevent_service.create_event(calendar_event)


@router.get("/calendar_events", response_model=list[CalendarRead])
def get_events():
    return calevent_service.get_events()


@router.get("/calendar_events/{calendar_event_id}", response_model=CalendarRead)
def get_event(calendar_event_id: int):
    result = calevent_service.get_event(calendar_event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.put(
    "/calendar_events/{calendar_event_id}",
    response_model=CalendarRead,
)
def update_event(calendar_event_id: int, calendar_event_data: CalendarUpdate):
    try:
        result = calevent_service.update_event(
            calendar_event_id,
            calendar_event_data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.delete(
    "/calendar_events/{calendar_event_id}",
    response_model=MessageResponse,
)
def delete_event(calendar_event_id: int):
    result = calevent_service.delete_event(calendar_event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

