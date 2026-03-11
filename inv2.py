import time
from system.lib.minescript import *
time.sleep(1)  # Inventar/Container öffnen vorher
items = container_get_items()  # oder player_inventory()
for i in items:
    print("slot:", i.slot, "item:", i.item, "nbt:", i.nbt)