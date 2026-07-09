import time
import schedule
from bot import run_bot


def start_scheduler():
    print("=" * 50)
    print("CoinDCX Auto Scheduler Started")
    print("=" * 50)

    # Bot ko har 15 minute chalaye
    schedule.every(15).minutes.do(run_bot)

    # Start hote hi ek baar run kare
    run_bot()

    while True:
        schedule.run_pending()
        time.sleep(1)