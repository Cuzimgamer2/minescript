import time
import random
import queue
import threading
import re
import sys

from system.lib.minescript import (
    execute,
    echo,
    container_get_items,
    screen_name,
    EventQueue,
    EventType,
)

from minescript_plus import Inventory, Screen
from lib_sign import Sign

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

"""
INFO
This is the website used to check the most profitable items:
https://www.skyblock.bz/npc

Filter for coins/hour.
Potatoes are usually around ~20m/h.
"""

ITEM_NAME      = "enchanted potato"
ITEM_ID        = "minecraft:baked_potato"
CUSTOM_AMOUNT  = "5k"

CLAIM_TIMEOUT  = 3
HOTKEY         = 54  # GLFW key code for key 6

# ──────────────────────────────────────────────────────────────
# UTILITIES
# ──────────────────────────────────────────────────────────────


def rand_sleep(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))


# ──────────────────────────────────────────────────────────────
# INVENTORY HELPERS
# ──────────────────────────────────────────────────────────────


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


# ──────────────────────────────────────────────────────────────
# BAZAAR ACTIONS
# ──────────────────────────────────────────────────────────────


def place_order(item_name: str):
    echo(f"Opening Bazaar for: {item_name}")

    execute(f"/bz {item_name}")
    rand_sleep(1.0, 1.8)

    # First item result
    Inventory.click_slot(11)
    echo("Selected item")

    rand_sleep(0.5, 1.0)

    # Buy order
    Inventory.click_slot(15)
    echo("Selected Buy Order")

    rand_sleep(1.1, 1.8)

    # Custom amount
    Inventory.click_slot(16)
    echo("Selected custom amount")

    rand_sleep(1.1, 1.8)

    # Write amount to sign GUI
    Sign.write(CUSTOM_AMOUNT, 0.05, 0.3, False, False)

    while Sign.is_writing():
        time.sleep(0.1)

    time.sleep(1)
    Sign.close_screen()

    echo(f"Entered custom amount: {CUSTOM_AMOUNT}")

    rand_sleep(1.1, 1.8)

    # Price adjustment nugget
    Inventory.click_slot(12)
    echo("Selected price adjustment")

    rand_sleep(1.1, 1.8)

    # Confirm order
    Inventory.click_slot(13)
    echo("Confirmed order")

    rand_sleep(0.5, 1.0)

    Screen.close_screen()



def claim_order():
    echo("Opening Bazaar to claim orders...")

    execute("/bz")
    rand_sleep(0.8, 1.5)

    # Your Orders
    Inventory.click_slot(50)
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
        echo("Claimed order item")

        rand_sleep(0.5, 1.0)

    Screen.close_screen()



def sell_items(item_id: str):
    echo(f"Selling items: {item_id}")

    execute("/boostercookie")
    rand_sleep(0.8, 1.5)

    while True:
        items = container_get_items() or []
        sellable_slot = None

        for it in items:
            nbt = (it.nbt or "").lower()

            # Ignore buyback slot
            if "click to buyback!" in nbt:
                continue

            if it.item == item_id or (it.item and item_id in it.item):
                sellable_slot = it.slot
                break

        if sellable_slot is None:
            break

        Inventory.click_slot(sellable_slot)
        echo(f"Sold item from slot {sellable_slot}")

        rand_sleep(0.3, 0.7)

    Screen.close_screen()


# ──────────────────────────────────────────────────────────────
# DAILY LIMIT MONITOR
# ──────────────────────────────────────────────────────────────


def start_daily_limit_killjob_monitor(run_once: bool = True):
    """
    Background monitor that watches chat for Hypixel daily-limit messages.
    If detected, all Minescript jobs are killed.
    """

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

                if (
                    ("daily limit" in cleaned and "coins" in cleaned)
                    or "you've reached the daily limit" in cleaned
                ):
                    echo("Daily limit detected. Killing all jobs.")

                    try:
                        execute(r"\killjob -1")
                    except Exception as ex:
                        echo(f"Failed to kill jobs: {ex}")

                    if run_once:
                        stop_event.set()
                        return

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()

    return stop_event


# ──────────────────────────────────────────────────────────────
# MAIN FLIPPER LOOP
# ──────────────────────────────────────────────────────────────


def main():
    time.sleep(5)

    echo("Bazaar Flipper started!")

    # Start safety monitor
    start_daily_limit_killjob_monitor()

    # Initial order
    try:
        place_order(ITEM_NAME)
    except Exception as e:
        echo(f"Error placing initial order: {e}")
    else:
        echo("Initial order placed.")

    with EventQueue() as events:
        events.register_chat_listener()
        events.register_key_listener()

        while True:
            echo("Waiting for order fill...")

            order_filled = False

            # Wait until order fills
            while not order_filled:
                event = events.get()

                if event is None:
                    continue

                if event.type == EventType.CHAT:
                    if "Buy Order" in event.message and "was filled" in event.message:
                        order_filled = True

            # Notification
            try:
                from minescript_plus import Gui

                Gui.set_title("§aOrder Filled!")
                Gui.set_subtitle(f"§ePress HOTKEY or wait {CLAIM_TIMEOUT}s")
                Gui.set_title_times(5, 80, 20)

            except Exception:
                echo("Order Filled! GUI unavailable")

            echo("Order filled — waiting for hotkey or timeout...")

            # Wait for hotkey OR timeout
            start = time.time()

            while time.time() - start < CLAIM_TIMEOUT:
                try:
                    event = events.get(timeout=0.1)

                    if (
                        event
                        and event.type == EventType.KEY
                        and event.key == HOTKEY
                    ):
                        echo("Hotkey pressed.")
                        break

                except queue.Empty:
                    pass

            # Clear GUI titles
            try:
                from minescript_plus import Gui
                Gui.clear_titles()
            except Exception:
                pass

            echo("Claiming order...")

            # Claim order
            try:
                claim_order()
            except Exception as e:
                echo(f"Error during claim: {e}")
            else:
                echo("Claim successful")

            rand_sleep(0.5, 1.0)

            # Sell items
            try:
                sell_items(ITEM_ID)
            except Exception as e:
                echo(f"Error during sell: {e}")
            else:
                echo("Sell successful")

            rand_sleep(1.5, 2.5)

            # Place new order
            echo("Placing new order...")

            try:
                place_order(ITEM_NAME)
            except Exception as e:
                echo(f"Error placing new order: {e}")


# ──────────────────────────────────────────────────────────────
# ENTRYPOINT
# ──────────────────────────────────────────────────────────────


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        echo("Script interrupted by user.")
    except Exception as e:
        echo(f"Fatal error: {e}")
    finally:
        echo("Script exited.")
