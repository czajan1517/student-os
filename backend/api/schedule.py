from fastapi import APIRouter, HTTPException, status

from backend.schemas.schedule import (
    ScheduleApplyResult,
    SchedulePreview,
    ScheduleRequest,
)
from backend.services.schedule_service import (
    ScheduleConflictError,
    ScheduleService,
    ScheduleTaskNotFoundError,
    ScheduleValidationError,
)


router = APIRouter(prefix="/schedule", tags=["schedule"])
schedule_service = ScheduleService()


@router.post("/preview", response_model=SchedulePreview)
def preview_task_schedule(request: ScheduleRequest):
    try:
        return schedule_service.preview_task(request)
    except ScheduleTaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error
    except ScheduleValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.post(
    "/apply",
    response_model=ScheduleApplyResult,
    status_code=status.HTTP_201_CREATED,
)
def apply_task_schedule(request: ScheduleRequest):
    try:
        return schedule_service.apply_task(request)
    except ScheduleTaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from error
    except ScheduleValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except ScheduleConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(error),
                "preview": error.preview.model_dump(mode="json"),
            },
        ) from error
