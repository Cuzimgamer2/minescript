import time
import minescript
from minescript_plus import Inventory, Screen
from system.lib.minescript import *
import sys

execute(f"/bz")
time.sleep(1)
Inventory.click_slot(50)
time.sleep(1)
Inventory.click_slot(19)
time.sleep(1)
print("bestellt")
time.sleep(0.5)
Screen.close_screen()
time.sleep(0.5)
print("finished")
