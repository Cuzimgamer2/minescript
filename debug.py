import sys
import queue
from minescript import EventQueue, EventType, execute

def matches_daily_limit(msg: str) -> bool:
    if not msg:
        return False
    m = msg.lower()
    return "daily limit" in m and "coins" in m or "you've reached the daily limit" in m

with EventQueue() as events:
    events.register_chat_listener()
    print("Waiting for daily-limit chat message...")
    while True:
        try:
            event = events.get(timeout=0.5)
        except queue.Empty:
            continue
        if event and event.type == EventType.CHAT:
            if matches_daily_limit(event.message):
                try:
                    execute("/say Detected daily limit of coins — stopping.")
                except Exception:
                    pass
                print("Detected daily limit, exiting.")
                sys.exit(0)