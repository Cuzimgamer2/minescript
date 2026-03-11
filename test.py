import time
import minescript
from minescript_plus import Inventory
from system.lib.minescript import *
import sys

open_bazaar = "/bz"
##

print("starte2222d")
time.sleep(2)
execute(f"/bz enchanted potato")
time.sleep(1)
Inventory.click_slot(11)
time.sleep(1)
Inventory.click_slot(15)
time.sleep(1)
Inventory.click_slot(14)
time.sleep(1)
Inventory.click_slot(12)
time.sleep(1)
Inventory.click_slot(13)
time.sleep(0.5)
print("finished")


