from system.lib.minescript import *
from minescript_plus import Inventory, Screen
import time

def find_and_click(item_id: str):
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

time.sleep(1)
execute(f"/boostercookie")
time.sleep(1)
if find_and_click("minecraft:baked_potato"):
    time.sleep(1)
    Screen.close_screen()
    print("geklickt")
else:
    print("nicht gefunden")