from sortBase import SortingAlgorithm

class MergeSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("Merge sort")

    @staticmethod
    def merge(left,right):
        if not left:
            return right
        if not right:
            return left

        result = []
        left_i = right_i = 0

        while len(result) < len(left) + len(right):
            if left[left_i] <= right[right_i]:
                result.append(left[left_i])
                left_i+=1
            else:
                result.append(right[right_i])
                right_i+=1

            if right_i == len(right):
                result += left[left_i:]
                break

            if left_i == len(left):
                result += right[right_i:]
                break

        return result

    def sort(self, array):
        if len(array) < 2:
            return array

        mid = len(array) // 2

        return self.merge( left = self.sort(array[:mid]), right=self.sort(array[mid:]) )



