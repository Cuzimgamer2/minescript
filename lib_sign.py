# This file is merely a way to simplify importing lib_sign into other minescript projects.
# For more details, check lib_sign's README.
from java import import_pyjinn_script
__lib_sign = import_pyjinn_script("lib_sign.pyj")
Sign = __lib_sign.get("Sign")()
