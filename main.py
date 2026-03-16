import time
import queue
import threading
import re
from minescript import EventQueue, EventType, echo, execute
import utils

# ── CONFIG ─────────────────────────────────────────────────────
 
"""
INFO 
This is the website i use to check the most profitable item (filter for coins/h) in general potatos are always around 20m/h but your welcome to try out another item
https://www.skyblock.bz/npc
"""

ITEM_NAME    = "enchanted potato"             # item to be bought from /bz
ITEM_ID      = "minecraft:baked_potato"       # Item-ID für Sell/Click
CLAIM_TIMEOUT = 3                           # Sekunden bis Auto-Claim (0 = nur Hotkey)
HOTKEY       = 54                           # GLFW code (54 = is 6) https://www.glfw.org/docs/3.3/group__keys.html
# ───────────────────────────────────────────────────────────────


echo("Flipper started!")

utils.start_daily_limit_killob_monitor()

try:
    utils.place_order(ITEM_NAME)
except Exception as e:
    echo(f"Error when placing order (utils.place_order): {e}")
else:
    echo("Placing initial order...")

with EventQueue() as events:
    events.register_chat_listener()
    events.register_key_listener()

    while True:
        echo("waiting for Order...")
        order_filled = False
        while not order_filled:
            event = events.get()
            if event is None:
                continue
            if event.type == EventType.CHAT:
                if "Buy Order" in event.message and "was filled" in event.message:
                    order_filled = True

        try:
            from minescript_plus import Gui
            Gui.set_title("§aOrder Filled!")
            Gui.set_subtitle("§epress TAB or wait {}s".format(CLAIM_TIMEOUT))
            Gui.set_title_times(5, 80, 20)
        except Exception:
            echo("§aOrder Filled! (GUI unavailable)")
        echo("Order filled — waiting for hotkey or timeout...")

        # waiting for hotkey OR timeout
        start = time.time()
        while True:
            try:
                event = events.get(timeout=0.1)
                if event and event.type == EventType.KEY and event.key == HOTKEY:
                    break
                if CLAIM_TIMEOUT > 0 and time.time() - start >= CLAIM_TIMEOUT:
                    break
            except queue.Empty:
                pass
            
        try:
            from minescript_plus import Gui
            Gui.clear_titles()
        except Exception:
            pass
        echo("Claiming order...")

        # claim + sell
        try:
            utils.claim_order()
        except Exception as e:
            echo(f"Error in claim: {e}")
        else:
            echo("Claim attempted")
        utils.rand_sleep(0.5, 1.0)
        try:
            utils.sell_items(ITEM_ID)
        except Exception as e:
            echo(f"Error in sell: {e}")
        else:
            echo("Sell attempted")
        utils.rand_sleep(1.5, 2.5)

        # new order being placed
        echo("§aNew order is being placed...")
        try:
            utils.place_order(ITEM_NAME)
        except Exception as e:
            echo(f"Error when placing new order: {e}")
echo("Script exited.")