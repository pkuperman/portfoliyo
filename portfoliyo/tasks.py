from celery import Celery
from celery.utils.log import get_task_logger
from django.conf import settings
from raven.contrib.celery import register_signal
from raven.contrib.django.models import client


logger = get_task_logger(__name__)



# automatic logging of task failures to Sentry
register_signal(client)



if settings.REDIS_URL: # pragma: no cover
    celery = Celery(
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        )  # pragma: no cover
else:
    celery = Celery()
    celery.conf.update(CELERY_ALWAYS_EAGER=True)

celery.conf.update(
    CELERY_DISABLE_RATE_LIMITS=True,
    CELERY_TIMEZONE=settings.TIME_ZONE,
    BROKER_POOL_LIMIT=settings.CELERY_BROKER_POOL_LIMIT,
    )


# set ignore_result=True for tasks where we don't care about the result
# set acks_late=True for tasks that are better executed twice than not at all

# if a task accesses DB rows created with the task, make sure the calling code
# commits the transaction before creating the task

@celery.task
def send_sms(phone, body):
    from portfoliyo import sms
    sms.send(phone, body)
