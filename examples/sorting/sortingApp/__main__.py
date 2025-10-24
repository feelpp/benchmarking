from argparse import ArgumentParser
from bubble import BubbleSort
from insertion import InsertionSort
from merge import MergeSort

if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument('-n',help="Number of elements",required=True)
    parser.add_argument('--algorithm','-a',type=str, help="Sorting algorithm to use",required=True)
    parser.add_argument('--out','-o',type=str, help="Filepath where to save elapsed times",required=True)
    parser.add_argument('--data-type','-t', type=str, help="Type of the data to sort (int,float,str)",default="int")
    args = parser.parse_args()

    n = int(float(args.n))

    if args.algorithm == "bubble":
        alg = BubbleSort()
    elif args.algorithm == "insertion":
        alg = InsertionSort()
    elif args.algorithm == "merge":
        alg = MergeSort()
    else:
        raise NotImplementedError(f"Sorting algorithm - {args.algorithm} - not implemented")

    array = alg.createRandomList(args.data_type,n)
    alg.tic()
    sorted = alg.sort(array)
    alg.toc()

    alg.save(args.out)

    alg.check(sorted)
