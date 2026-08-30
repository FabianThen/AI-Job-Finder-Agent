from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler(job_function):
    """
    Start the APScheduler to run the job function every day at 5:00 AM.
    
    Args:
        job_function: The function to execute daily.
    """
    scheduler = BlockingScheduler()
    
    # Run every day at 5:00 AM
    trigger = CronTrigger(hour=5, minute=0)
    
    scheduler.add_job(job_function, trigger)
    logger.info("Scheduler started. Job will run daily at 5:00 AM.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
