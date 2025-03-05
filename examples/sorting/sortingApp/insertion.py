from sortBase import SortingAlgorithm

class InsertionSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Insertion sort")

    def sort(self, array):
        n = len(array)

        for i in range(1,n):
            key_item = array[i]
            j = i - 1

            while j>=0 and array[j] > key_item:
                array[j+1]=array[j]
                j-=1
            array[j+1] = key_item

        return array