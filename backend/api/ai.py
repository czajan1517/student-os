from fastapi import APIRouter, Depends, HTTPException, status

from backend.ai.task_classifier import (
    AIConfigurationError,
    TaskClassificationError,
    TaskClassifier,
)
from backend.schemas.ai import TaskClassification, TaskClassificationRequest


router = APIRouter(prefix="/ai", tags=["ai"])
task_classifier = TaskClassifier()


def get_task_classifier() -> TaskClassifier:
    return task_classifier


@router.post(
    "/tasks/classify",
    response_model=TaskClassification,
)
def classify_task(
    request: TaskClassificationRequest,
    classifier: TaskClassifier = Depends(get_task_classifier),
):
    try:
        return classifier.classify_task(request)
    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except TaskClassificationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
