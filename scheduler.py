import time
import schedule
import traceback
from datetime import datetime

from bot import run_bot


def safe_run_bot():
    """Wrapper to catch errors so scheduler doesn't die."""

    try:
        print(
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            "Running bot..."
        )

        run_bot()

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            "Bot finished successfully"
        )

    except Exception as e:
        print(f"\n[ERROR] Bot crashed: {e}")
        traceback.print_exc()

        # Telegram alert yahan enable kar sakte ho
        # send_telegram_message(f"⚠️ Bot Crashed: {e}")


def start_scheduler():
    print("=" * 50)
    print("CoinDCX Auto Scheduler Started")
    print("Strategy Timeframe: 1 Minute")
    print("Strategy: SMA44 + Candle Confirmation + Volume")
    print("=" * 50)

    # Run bot every 1 minute
    schedule.every(1).minute.do(safe_run_bot)

    # Run once immediately when bot starts
    safe_run_bot()

    # Scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    start_scheduler()

