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

CLAIM_TIMEOUT        = 3
ORDER_TIMEOUT        = 120
MAX_CONCURRENT_ORDERS = 5
HOTKEY               = 54  # GLFW key code for key 6
ORDER_CONFIRM_TIMEOUT = 8

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


def place_order(item_name: str, events: EventQueue = None) -> bool:
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
    echo("Waiting for Bazaar confirmation message...")

    confirmed = False

    # Wait for confirmation chat message
    if events is not None:
        start = time.time()

        while time.time() - start < ORDER_CONFIRM_TIMEOUT:
            try:
                event = events.get(timeout=0.25)
            except queue.Empty:
                continue

            if not event or event.type != EventType.CHAT:
                continue

            cleaned = re.sub(r'§.', '', (event.message or '')).lower()

            if "buy order setup" in cleaned:
                confirmed = True
                break

    rand_sleep(0.5, 1.0)

    Screen.close_screen()

    if confirmed:
        echo("Order successfully confirmed by Bazaar chat message.")
    else:
        echo("Order confirmation message not detected.")

    return confirmed



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

    concurrent_orders = 0
    last_order_time = 0

    # Create event queue BEFORE first order
    # otherwise the first confirmation message gets missed
    with EventQueue() as events:
        events.register_chat_listener()
        events.register_key_listener()

        # Initial order
        try:
            if place_order(ITEM_NAME, events):
                concurrent_orders += 1
                last_order_time = time.time()

                echo(
                    f"Initial order confirmed | "
                    f"Active Orders: {concurrent_orders}/{MAX_CONCURRENT_ORDERS}"
                )
            else:
                echo("Initial order was NOT confirmed.")

        except Exception as e:
            echo(f"Error placing initial order: {e}")


        events.register_chat_listener()
        events.register_key_listener()

        while True:
            current_time = time.time()

            # Timeout-based new order placement
            if (
                concurrent_orders < MAX_CONCURRENT_ORDERS
                and current_time - last_order_time >= ORDER_TIMEOUT
            ):
                echo(
                    f"Order timeout reached ({ORDER_TIMEOUT}s). "
                    f"Placing another order..."
                )

                try:
                    if place_order(ITEM_NAME, events):
                        concurrent_orders += 1
                        last_order_time = time.time()

                    echo(
                        f"Timeout order placed | "
                        f"Active Orders: {concurrent_orders}/{MAX_CONCURRENT_ORDERS}"
                    )

                except Exception as e:
                    echo(f"Failed to place timeout order: {e}")

            # Process events continuously
            try:
                event = events.get(timeout=0.25)
            except queue.Empty:
                continue

            if event is None:
                continue

            # Filled order detection
            if event.type == EventType.CHAT:
                if "Buy Order" in event.message and "was filled" in event.message:

                    concurrent_orders = max(0, concurrent_orders - 1)

                    echo(
                        f"Order filled | "
                        f"Active Orders: {concurrent_orders}/{MAX_CONCURRENT_ORDERS}"
                    )

                    # Notification
                    try:
                        from minescript_plus import Gui

                        Gui.set_title("§aOrder Filled!")
                        Gui.set_subtitle(
                            f"§ePress HOTKEY or wait {CLAIM_TIMEOUT}s"
                        )
                        Gui.set_title_times(5, 80, 20)

                    except Exception:
                        echo("Order Filled! GUI unavailable")

                    # Wait for hotkey OR timeout
                    start = time.time()

                    while time.time() - start < CLAIM_TIMEOUT:
                        try:
                            key_event = events.get(timeout=0.1)

                            if (
                                key_event
                                and key_event.type == EventType.KEY
                                and key_event.key == HOTKEY
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

                    # Claim order
                    echo("Claiming order...")

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

                    # Place replacement order immediately after fill
                    if concurrent_orders < MAX_CONCURRENT_ORDERS:
                        echo("Placing replacement order...")

                        try:
                            if place_order(ITEM_NAME, events):
                                concurrent_orders += 1
                                last_order_time = time.time()

                            echo(
                                f"Replacement order placed | "
                                f"Active Orders: {concurrent_orders}/{MAX_CONCURRENT_ORDERS}"
                            )

                        except Exception as e:
                            echo(f"Error placing replacement order: {e}")
                    else:
                        echo(
                            "Replacement order skipped: "
                            "max concurrent orders reached"
                        )


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
