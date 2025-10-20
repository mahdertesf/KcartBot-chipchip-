from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


def check_expiring_stock_job():
    """
    Job that runs the check_expiring_stock management command.
    """
    try:
        logger.info("Running check_expiring_stock job...")
        call_command('check_expiring_stock', '--days=7')
        logger.info("check_expiring_stock job completed successfully")
    except Exception as e:
        logger.error(f"Error running check_expiring_stock job: {e}")


def start_scheduler():
    """
    Starts the APScheduler for periodic tasks.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Schedule the expiring stock check to run every 5 minutes (for demo purposes)
    # In production, you might want to run this once or twice a day
    scheduler.add_job(
        check_expiring_stock_job,
        'interval',
        minutes=5,
        id='check_expiring_stock',
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")

