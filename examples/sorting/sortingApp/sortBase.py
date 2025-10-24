import numpy as np
from time import perf_counter
import json, os

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None

    def tic(self):
        self.start_time = perf_counter()

    def toc(self):
        self.end_time = perf_counter()
        self.elapsed_time = self.end_time - self.start_time


    def saveTime(self, filepath):
        if not filepath.endswith(".json"):
            filepath += ".json"
        dir = os.path.dirname(filepath)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
        with open(filepath,"w") as f:
            json.dump({"elapsed":self.elapsed_time},f)

class SortingAlgorithm:
    def __init__(self,name):
        self.name = name
        self.timer = Timer()

    @staticmethod
    def createRandomList(type,n):
        if type == "int":
            return np.random.randint(min(-1000,-n),max(1000,n),n).tolist()
        elif type == "float":
            return np.random.uniform(min(-1000,-n),max(1000,n),n).tolist()
        else:
            raise NotImplementedError(f"Type {type} not implemented")

    def tic(self):
        self.timer.tic()

    def toc(self):
        self.timer.toc()
        print(f"Sorting algorithm - {self.name} - took {self.timer.elapsed_time} s")

    def save(self,filepath):
        self.timer.saveTime(filepath)

    def check(self,array):
        assert sorted(array) == array, "Array is not sorted"