import time
import random
from minescript import execute, echo, container_get_items, screen_name
from minescript_plus import Inventory, Screen, Gui
from system.lib.minescript import *
import sys
from pynput.keyboard import Key, Controller

keyboard = Controller()

# ── CONFIG ─────────────────────────────────────────────────────

CUSTOM_AMOUNT = "1k"

# ── CONFIG ─────────────────────────────────────────────────────

def rand_sleep(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))

def find_and_click(item_id: str) -> bool:
    if screen_name() is not None:
        slot = Inventory.find_item(item_id, container=True)
        if slot is not None:
            Inventory.click_slot(slot)
            return True
        slot = Inventory.find_item(item_id)
        if slot is not None:
            Inventory.click_slot(slot + len(container_get_items() or []))
            return True
    slot = Inventory.find_item(item_id)
    if slot is not None:
        Inventory.click_slot(slot)
        return True
    return False

def place_order(item_name: str):
    execute(f"/bz {item_name}")
    rand_sleep(1.0, 1.8)
    
    Inventory.click_slot(11) #1 slot in the bazaar maybe edit it if the /bz {item_name} is not enough to only show 1 item (yours)
    print("potato")
    rand_sleep(0.5, 1.0)
    Inventory.click_slot(15)
    print("buy order")
    
    rand_sleep(1.1, 1.8)
    Inventory.click_slot(16)
    print("custom amount")
    
    rand_sleep(1.1, 1.8)
    keyboard.type(CUSTOM_AMOUNT)
    print("custom enterd")
    
    rand_sleep(0.5, 1.0)
    keyboard.press(Key.esc)
    keyboard.release(Key.esc)
    
    rand_sleep(1.1, 1.8)
    Inventory.click_slot(12)
    print("nugget")
    
    rand_sleep(1.1, 1.8)
    Inventory.click_slot(13)
    print("confirm")
    
    rand_sleep(0.5, 1.0)
    Screen.close_screen()

def claim_order():
    execute("/bz")
    rand_sleep(0.8, 1.5)
    Inventory.click_slot(50)  # your orders
    rand_sleep(0.8, 1.5)

    while True:
        items = container_get_items() or []
        slot_item = next((it for it in items if it.slot == 19), None)
        if slot_item is None:
            break
        nbt = (slot_item.nbt or "").lower()
        if "click to buyback!" in nbt:
            break
        Inventory.click_slot(19)
        rand_sleep(0.5, 1.0)

    Screen.close_screen()

def sell_items(item_id: str):
    execute(f"/boostercookie")
    rand_sleep(0.8, 1.5)
    
    while True:
        items = container_get_items() or []
        sellable_slot = None

        # Search container slots for the desired item that is NOT the buyback slot
        for it in items:
            # `it` has attributes like `item`, `count`, `nbt`, `slot`
            # Skip None nbt safely
            nbt = (it.nbt or "").lower()
            if "click to buyback!" in nbt: # If this slot shows the buyback prompt, skip it
                continue
            if it.item == item_id or (it.item and item_id in it.item): # Match by item id (some item strings may include namespace)
                sellable_slot = it.slot
                break

        if sellable_slot is None:
            break

        Inventory.click_slot(sellable_slot)
        rand_sleep(0.3, 0.7)

    Screen.close_screen()

def start_daily_limit_killob_monitor(run_once: bool = True):
    """
    Startet einen Hintergrund-Thread, der dauerhaft den Chat auf die
    Daily-Limit-Nachricht prüft. Bei Treffer wird `/killob -1` ausgeführt.
    Wenn `run_once` True ist, stoppt der Monitor nach dem ersten Treffer.
    Gibt ein threading.Event zurück (optional zum Abfragen/Stoppen).
    """
    import threading, re, queue
    from minescript import EventQueue, EventType, execute

    stop_event = threading.Event()

    def _monitor():
        with EventQueue() as ev:
            ev.register_chat_listener()
            while not stop_event.is_set():
                try:
                    e = ev.get(timeout=0.5)
                except queue.Empty:
                    continue
                if not e or e.type != EventType.CHAT:
                    continue
                cleaned = re.sub(r'§.', '', (e.message or '')).lower().replace("’", "'")
                if ("daily limit" in cleaned and "coins" in cleaned) or "you've reached the daily limit" in cleaned:
                    try:
                        execute("\killjob -1")
                    except Exception:
                        pass
                    if run_once:
                        stop_event.set()
                        return

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()
    return stop_event