from fastapi import APIRouter

router = APIRouter(
    prefix="/processing-jobs",
    tags=["Processing Jobs"],
)