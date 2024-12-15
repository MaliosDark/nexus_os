import schedule
import time

def schedule_task(time_str, task, *args, **kwargs):
    schedule.every().day.at(time_str).do(task, *args, **kwargs)
    print(f"Task scheduled at {time_str}")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
