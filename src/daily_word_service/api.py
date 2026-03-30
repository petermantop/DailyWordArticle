from fastapi import APIRouter, Depends, HTTPException, status

from daily_word_service.container import get_service
from daily_word_service.exceptions import ServiceError
from daily_word_service.schemas import Article, HealthResponse
from daily_word_service.service import WordOfTheDayService


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(service: WordOfTheDayService = Depends(get_service)) -> HealthResponse:
    return service.health()


@router.get("/word-of-the-day", response_model=Article)
def read_word_of_the_day(
    service: WordOfTheDayService = Depends(get_service),
) -> Article:
    try:
        return service.get_article()
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/word-of-the-day/refresh", response_model=Article)
def refresh_word_of_the_day(
    service: WordOfTheDayService = Depends(get_service),
) -> Article:
    try:
        return service.refresh_article()
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

