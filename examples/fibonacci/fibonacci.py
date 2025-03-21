from argparse import ArgumentParser
import os
from time import perf_counter

def fibonacciRecursive(n):
    if n < 1: return 0
    elif n <= 2: return 1
    else: return fibonacciRecursive(n-1) + fibonacciRecursive(n-2)

def fibonacciIterative(n):
    if n < 1: return 0
    elif n <= 2: return 1
    else:
        a,b = 1,1
        for i in range(3,n+1):
            a,b = b,a+b
        return b


if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument('-n',type=int,help="Sequence number",required=True)
    parser.add_argument('--approach','-a',type=str, help="Fibonacci algorithm approach to use",required=True)
    parser.add_argument('--out','-o',type=str, help="Filepath where to save elapsed times",required=True)
    args = parser.parse_args()

    n = int(args.n)

    if args.approach == "recursive":
        fib = fibonacciRecursive
    elif args.approach == "iterative":
        fib = fibonacciIterative
    else:
        raise NotImplementedError(f"Fibonacci approach - {args.approach} - not implemented")


    tic = perf_counter()
    fib_number = fib(n)
    toc = perf_counter()
    elapsed_time = toc - tic


    dirpath = os.path.dirname(args.out)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    with open(args.out,'w') as f:
        f.write(f"elapsed,fibonacci_number\n{elapsed_time},{fib_number}")

    print(f"Elapsed time: {elapsed_time}")
    print(f"Fibonacci number: {fib_number}")
    print("Done!")