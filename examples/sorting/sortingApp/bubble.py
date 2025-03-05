from sortBase import SortingAlgorithm

class BubbleSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Bubble sort")

    def sort(self, array):
        n = len(array)
        is_sorted = True
        for i in range(n):
            for j in range( n - i - 1 ):
                if array[j] > array[j+1]:
                    array[j],array[j+1] = array[j+1], array[j]
                    is_sorted = False
            if is_sorted:
                break

        return array


