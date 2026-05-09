from celery import Celery
from app.settings import Config

app = Celery(
    "app_worker",
    broker=Config.REDIS_URL,  # Ensure this is in your Config
    backend=Config.REDIS_URL
)

# Discover tasks from your task module
app.autodiscover_tasks(['app.queue.task'])
app.config_from_object("app.settings")

app.conf.update(
    beat_dburi=Config.DB_URL,
    beat_schema='celery_schema',
    worker_pool='prefork',
    task_track_started=True,
)

app.conf.timezone = 'Asia/Kolkata'
