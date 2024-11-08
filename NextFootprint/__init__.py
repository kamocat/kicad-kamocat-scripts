# Two way of installation of this plugin:
#  - Copy or link this directory to KiCad plugin directory (~/.kicad_plugin/NextFootprint/)
#  - Copy files to ~/.kicad_plugin except __init__.py...
from __future__ import print_function
import pprint
import traceback
import sys

print("Starting plugin NextFootprint")
try:
    from .nextfp import *
except Exception as e:
    traceback.print_exc(file=sys.stdout)
    pprint.pprint(e)
