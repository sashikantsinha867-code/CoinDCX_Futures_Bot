import time
import schedule
import traceback
from datetime import datetime
from bot import run_bot

def safe_run_bot():
    """Wrapper to catch errors so scheduler doesn't die"""
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running bot...")
        run_bot()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot finished successfully")
    except Exception as e:
        print(f"\n[ERROR] Bot crashed: {e}")
        traceback.print_exc()
        # Telegram alert bhi bhej sakte ho yaha
        # send_telegram_message(f"⚠️ Bot Crashed: {e}")

def start_scheduler():
    print("=" * 50)
    print("CoinDCX Auto Scheduler Started")
    print("=" * 50)

    # Bot ko har 15 minute chalaye
    schedule.every(15).minutes.do(safe_run_bot)

    # Start hote hi ek baar run kare
    safe_run_bot()

    while True:
        schedule.run_pending()
        time.sleep(30)  # 1 sec ki jagah 30 sec. CPU kam use hoga

if __name__ == "__main__":
    start_scheduler()