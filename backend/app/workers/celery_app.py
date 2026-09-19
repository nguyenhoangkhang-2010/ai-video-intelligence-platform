import os

from celery import Celery


celery_app = Celery(
    "ai_video",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/0",
    ),
    backend=os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/0",
    ),
    include=[
        "app.workers.video_processor",
    ],
)

celery_app.conf.update(
    task_track_started=True,
)