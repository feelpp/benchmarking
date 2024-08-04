from src.feelpp.benchmarking.configReader   import ConfigReader
from argparse                               import ArgumentParser
from datetime                               import datetime
import sys
import os
import json
import shutil


validMachines = ('discoverer', 'gaya', 'karolina', 'meluxina', 'local')     # config-files missing for discoverer, karolina, meluxina


# +--------------------------------------+
# |           ARGS VALIDATION            |
# +--------------------------------------+

def parseArgs():        # Complicated usage presentation (because of extend?), could maybe be enhanced

    parser = ArgumentParser()
    parser.add_argument('machine', type=str, help='Name of the machine')
    parser.add_argument('--config', '-c', type=str, action='extend', nargs='+', help='Path to the JSON configuration file')
    parser.add_argument('--dir', '-d', type=str, action='extend', nargs='+', help='Name of the directory containing JSON configuration file(s)')
    parser.add_argument('--list', '-l', action='store_true', help='List tests that will be run by Reframe')
    parser.add_argument('--verbose', '-v', action='store_true', help='Run with Reframe\'s verbose')

    args = parser.parse_args()
    args.config = handleColonSeparator(args.config)

    argsValidation(args)
    printArgs(args)

    return args


# not really useful as arguments can be passed multiple times with blank space or multiple -c
def handleColonSeparator(arg):
    splitted = []
    if isinstance(arg, list):
        for elem in arg:
            if ':' in elem:
                splitted.extend(elem.split(':'))
            else:
                splitted.append(elem)
        arg = splitted

    elif isinstance(arg, str):
        if ':' in arg:
            splitted.append(arg.split(':'))
    return arg


def argsValidation(args):
    if args.machine not in validMachines:
        print('[Error] Unknown machine:', args.machine)
        print('Valid machines are:', validMachines)
        sys.exit(1)

    if not args.config and not args.dir:
        print(f'[Error] At least one of --config or --dir option must be specified')
        sys.exit(1)

    if args.config:
        for config in args.config:
            if not os.path.exists(config):
                print(f'[Error] Configuration file "{config}" not found')
                sys.exit(1)

    if args.dir:
        for dir in args.dir:
            if not os.path.isdir(dir):
                print(f'[Error] Directory {args.dir} not found')
                sys.exit(1)



def printArgs(args):
    print('\n[LAUNCHER] Loaded command-line options:')
    print(f'{" > Machine:":<20} {args.machine}')
    if args.dir:
        print(f'{" > Directory:":<20} {args.dir}')
    if args.config:
        print(f'{" > Config:":<20} {args.config}')
    print(f'{" > Listing:":<20} {args.list}')
    print(f'{" > Verbose:":<20} {args.verbose}\n')


def pathBuilder():
    """ --- Issue adressed to Reframe Dev-Team for manipulating report-path from within a test --- """
    return #TODO


def varExporter(configPath):
    with open(configPath, 'r') as file:
        data = json.loads(file)

    print(data['Reframe'])



# +------------------------------------+
# |              MAIN                  |
# +------------------------------------+


# Needed for report-file (if passed from CL)
date = datetime.now()
date = date.strftime("%Y%m%d")

args = parseArgs()


""" --- Export some needed ENV_VARS --- """

workdir = os.getcwd()
home = os.getenv('HOME')

os.environ['WORKDIR'] = workdir
os.environ['HOSTNAME'] = args.machine
#os.environ['RFM_TEST_DIR'] = os.path.join(workdir, 'src/feelpp/benchmarking/reframe/regression-tests')
os.environ['FEELPPDB_PATH'] = '/data/scratch/pierre/feelppdb'
os.environ['RFM_PREFIX'] = os.path.join(workdir, 'build/bench/')


counter = 0
for configPath in args.config:
    os.environ['CONFIG_PATH'] = configPath
    configName = os.path.basename(configPath)


    cmd = [ f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/reframeConfig.py',
            f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/{args.machine}.py',
            f'-c {workdir}/src/feelpp/benchmarking/reframe/regression-tests/cpuVariation.py',
            f'--system={args.machine}',
             '--exec-policy=async',    #async/serial
            f'--report-file={workdir}/docs/modules/{args.machine}/pages/reports/{date}-{configName}' ]

    cmd += ['-l'] if args.list else ['-r']
    if args.verbose:
        cmd += ['-v']

    os.system(' '.join(['reframe'] + cmd))
    print('=' * shutil.get_terminal_size().columns)
    counter += 1


print("\n > Number of tests run:\t", counter)