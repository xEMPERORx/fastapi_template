from celery import Celery
from celery.schedules import crontab
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
    # Nothing in this app ever calls .get() on a task result, so there is no
    # reason to pay for the Redis result backend at all. Critically, without
    # this, every .delay() call makes Celery set up a result-tracking pubsub
    # subscription (on_task_call -> result_consumer.consume_from) that retries
    # over time internally and can block for a very long time if Redis is
    # unreachable — independent of any socket-level timeout.
    task_ignore_result=True,
    # Defense in depth: bound the broker (task-sending) connection too, so a
    # totally unreachable Redis fails fast instead of hanging the caller.
    broker_transport_options={"socket_connect_timeout": 3, "socket_timeout": 3},
    broker_connection_timeout=3,
)

app.conf.timezone = 'Asia/Kolkata'

app.conf.beat_schedule = {
    "cleanup-expired-refresh-tokens": {
        "task": "cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
}
