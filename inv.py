import minescript
from system.lib.minescript import *
import time

time.sleep(10)
list = minescript.container_get_items()
for i in list:
  minescript.echo(f"slot, {i.slot}, item, {i.item}")