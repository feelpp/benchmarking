import sys
import os

print("\n[TEST 1]")


root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
grandParent = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(" > root:\t", root)
print(" > parent:\t", grandParent, "\n")

sys.path.insert(0, root)
sys.path.insert(0, grandParent)

from src.feelpp.benchmarking.configReader import ConfigReader

print("[TEST 2]")
config = ConfigReader()
print("[TEST 3]")