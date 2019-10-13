# Workaround to make ../sedparse.py importable from all test scripts.
# Idea from https://www.kennethreitz.org/essays/repository-structure-and-python

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position,unused-import,unused-variable
import sedparse
