import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(HERE))  # the repo root, for text2graph
sys.path.insert(0, HERE)                   # for fake_hou
