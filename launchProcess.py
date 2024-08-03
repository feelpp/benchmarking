from src.feelpp.benchmarking.configReader   import ConfigReader
from argparse                               import ArgumentParser
from datetime                               import datetime
import sys
import os
import json
import shutil


validMachines = ('discoverer', 'gaya', 'karolina', 'meluxina', 'local')     # config-files missing for discoverer, karolina, meluxina
validToolboxes = ('alemesh', 'coefficientformpdes', 'electric', 'fluid', 'fsi', 'hdg', 'heat', 'heatfluid', 'solid', 'thermoelectric')
validModes = ('CpuVariation', 'ModelVariation', 'TEST')         # Model not working yet


# +--------------------------------------+
# |           ARGS VALIDATION            |
# +--------------------------------------+

def parseArgs():        # Complicated usage presentation (because of extend?), could maybe be enhanced

    parser = ArgumentParser()
    parser.add_argument('machine', type=str, help='Name of the machine')
    parser.add_argument('--config', '-c', type=str, action='extend', nargs='+', required=True, help='Path to the desired benchmark configuration file')
    parser.add_argument('--list', '-l', action='store_true', help='List found .cfg files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Run with Reframe\'s verbose')

    """ Check what is needed """
    #parser.add_argument('--toolboxes', '-tb', type=str, action='extend', nargs='+', help='Name of the toolbox (multiple names separated by :)')
    #parser.add_argument('--all', '-a', action='store_true', help='Launch every test of every toolbox')
    #parser.add_argument('--case', '-c', type=str, action='extend', nargs='+', help='Name of the case .cfg file (multiple names separated by :, requires -tb)')
    #parser.add_argument('--dir', '-d', type=str, action='extend', nargs='+', help='Name of the directory containing .cfg (multiple names separated by :, requires -tb)')
    #parser.add_argument('--recursive', '-r', action='store_true', help='Launching every .cfg file from DIR')
    #parser.add_argument('--mode', '-m', type=str, action='extend', nargs='+', required=True, help='Select Reframe\'s mode to run')

    args = parser.parse_args()
    args.config = handleColonSeparator(args.config)

    argsValidation(args)
    #printArgs(args)

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

    """
    if args.toolboxes:
        for toolbox in args.toolboxes:
            if toolbox not in validToolboxes:
                print('[Error] Unknown toolbox:', args.toolboxes)
                print('Valid toolboxes are:', validToolboxes)
                sys.exit(1)

    if args.mode:
        for mode in args.mode:
            if mode not in validModes:
                print('[Error] Unknown mode:', args.mode)
                print('Valid modes are:', validModes)
                sys.exit(1)

    if (args.case or args.dir) and not args.toolboxes:
        print('[Error] --case and --dir options require --toolbox to be specified')
        sys.exit(1)
    """


def printArgs(args):
    print('\n[LOADED COMMAND LINE OPTIONS]')
    print(f'{" > Machine:":<20} {args.machine}')
    print(f'{" > Toolbox:":<20} {args.toolboxes}')
    print(f'{" > Case:":<20} {args.case}')
    print(f'{" > Directory:":<20} {args.dir}')
    print(f'{" > Mode:":<20} {args.mode}')
    print(f'{" > All:":<20} {args.all}')
    print(f'{" > Listing:":<20} {args.list}')


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

"""
TO BE DONE:     * --config-files list of list in JSON for multiple cases launching
                * toolbox / case / dir combination
                * look up --ci-generate
                * loop for .cfg files
                * usage presentation
"""

# Needed for report-file (if passed from CL)
date = datetime.now()
date = date.strftime("%Y%m%d")

args = parseArgs()


""" --- Export some needed ENV_VARS --- """

workdir = os.getcwd()
home = os.getenv('HOME')

os.environ['WORKDIR'] = workdir
os.environ['HOSTNAME'] = args.machine
os.environ['RFM_TEST_DIR'] = os.path.join(workdir, 'src/feelpp/benchmarking/reframe/regression-tests')
os.environ['FEELPPDB_PATH'] = os.path.join(home, 'feelppdb')
os.environ['RFM_PREFIX'] = os.path.join(workdir, 'build/loopTest')          # ou: os.path.join(os.environ['WORKDIR'], 'build/loop')


counter = 0
for configPath in args.config:
    os.environ['CONFIG_PATH'] = configPath
    configName = os.path.basename(configPath)

    cmd = [ f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/reframeConfig.py',
            f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/{args.machine}.py',
            f'-c {workdir}/src/feelpp/benchmarking/reframe/regression-tests/cpuVariation.py',
            f'--system={args.machine}',
             '--exec-policy=serial',    #async/serial
            f'--report-file={workdir}/build/{date}-{configName}' ]

    cmd += ['-l'] if args.list else ['-r']
    if args.verbose:
        cmd += ['-v']

    os.system(' '.join(['reframe'] + cmd))
    print('=' * shutil.get_terminal_size().columns)
    counter += 1


print("\n > Number of tests run:\t", counter)