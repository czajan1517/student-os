from fastapi import APIRouter, Depends, HTTPException, status

from backend.ai.chat_responder import ChatResponder, ChatResponseError
from backend.ai.ollama_client import (
    AIConfigurationError,
    AIProviderUnavailableError,
)
from backend.ai.task_classifier import (
    TaskClassificationError,
    TaskClassifier,
)
from backend.schemas.ai import (
    ChatRequest,
    ChatResponse,
    TaskClassification,
    TaskClassificationRequest,
)


router = APIRouter(prefix="/ai", tags=["ai"])
task_classifier = TaskClassifier()
chat_responder = ChatResponder()


def get_task_classifier() -> TaskClassifier:
    return task_classifier


def get_chat_responder() -> ChatResponder:
    return chat_responder


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
    except (AIConfigurationError, AIProviderUnavailableError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except TaskClassificationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error


@router.post(
    "/respond",
    response_model=ChatResponse,
)
def respond_to_chat(
    request: ChatRequest,
    responder: ChatResponder = Depends(get_chat_responder),
):
    try:
        return responder.respond(request)
    except (AIConfigurationError, AIProviderUnavailableError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except ChatResponseError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
