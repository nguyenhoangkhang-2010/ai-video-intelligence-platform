from celery import Celery

celery_app = Celery(
    "ai_video",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "app.workers.video_processor",
    ],
)

celery_app.conf.update(
    task_track_started=True,
)