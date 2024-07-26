from src.feelpp.benchmarking.configReader   import ConfigReader
from argparse                               import ArgumentParser
from datetime                               import datetime
import sys
import os
import subprocess
import shutil


validMachines = ('discoverer', 'gaya', 'karolina', 'meluxina', 'local')     # config-files missing for discoverer, karolina, meluxina
validToolboxes = ('alemesh', 'coefficientformpdes', 'electric', 'fluid', 'fsi', 'hdg', 'heat', 'heatfluid', 'solid', 'thermoelectric')
validModes = ('CpuVariation', 'ModelVariation', 'TEST')         # Model not working yet


def parseArgs():        # Usage presentation to be enhanced (because of extend?)

    parser = ArgumentParser()
    parser.add_argument('machine', type=str, help='Name of the machine')
    parser.add_argument('--all', '-a', action='store_true', help='Launch every test of every toolbox')
    parser.add_argument('--toolboxes', '-tb', type=str, action='extend', nargs='+', help='Name of the toolbox (multiple names separated by :)')
    parser.add_argument('--case', '-c', type=str, action='extend', nargs='+', help='Name of the case .cfg file (multiple names separated by :, requires -tb)')
    parser.add_argument('--dir', '-d', type=str, action='extend', nargs='+', help='Name of the directory containing .cfg (multiple names separated by :, requires -tb)')
    parser.add_argument('--list', '-l', action='store_true', help='List found .cfg files')
    parser.add_argument('--mode', '-m', type=str, action='extend', nargs='+', required=True, help='Select Reframe\'s mode to run')
    #parser.add_argument('--recursive', '-r', action='store_true', help='Launching every .cfg file from DIR')

    args = parser.parse_args()
    args.toolboxes, args.case, args.dir, args.mode = handleColonSeparator([args.toolboxes, args.case, args.dir, args.mode])

    argsValidation(args)
    #printArgs(args)

    return args


def handleColonSeparator(argList):
    result = []
    for arg in argList:
        if arg is None:
            result.append(None)

        elif isinstance(arg, list):
            splitted = []
            for elem in arg:
                if ':' in elem:
                    splitted.extend(elem.split(':'))
                else:
                    splitted.append(elem)
            result.append(splitted)

        elif isinstance(arg, str):
            if ':' in arg:
                result.append(arg.split(':'))
            else:
                result.append([arg])
    return result


def argsValidation(args):
    if args.machine not in validMachines:
        print('[Error] Unknown machine:', args.machine)
        print('Valid machines are:', validMachines)
        sys.exit(1)

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

    if args.case:
        for case in args.case:
            if case[-4:] != '.cfg':
                print("Invalid .cfg file:", case)
                sys.exit(1)

    if (args.case or args.dir) and not args.toolboxes:
        print('[Error] --case and --dir options require --toolbox to be specified')
        sys.exit(1)


def printArgs(args):
    print('\n[LOADED COMMAND LINE OPTIONS]')
    print(f'{" > Machine:":<20} {args.machine}')
    print(f'{" > Toolbox:":<20} {args.toolboxes}')
    print(f'{" > Case:":<20} {args.case}')
    print(f'{" > Directory:":<20} {args.dir}')
    print(f'{" > Mode:":<20} {args.mode}')
    print(f'{" > All:":<20} {args.all}')
    print(f'{" > Listing:":<20} {args.list}')


def pathBuilder():  # For report-path
    return #TODO


def envVarsDebug():
    hostname = os.getenv('HOSTNAME')
    workdir = os.getenv('WORKDIR')
    rfmConfig = os.getenv('RFM_CONFIG_FILES')
    minCPU = os.getenv('MIN_CPU')
    maxCPU = os.getenv('MAX_CPU')
    minNodes = os.getenv('MIN_NODES')
    maxNodes = os.getenv('MAX_NODES')

    print('\n[ENV_TEST]')
    print(' > HOSTNAME:\t', hostname)
    print(' > WORKDIR:\t', workdir)
    print(' > RFM_CONFIG_FILES:\t', rfmConfig)
    print(' > MIN_CPU:\t', minCPU)
    print(' > MAX_CPU:\t', maxCPU)
    print(' > MIN_NODES:\t', minNodes)
    print(' > MAX_NODES:\t', maxNodes)



# +------------------------------------+
# |              MAIN                  |
# +------------------------------------+

"""
TO BE DONE:     * --config-files list of list in JSON for multiple cases launching
                * toolbox / case / dir combination
                * look up --ci-generate
                * recursive look for .cfg files
                * usage presentation
"""


date = datetime.now()
date = date.strftime("%Y%m%d")
reframePath = shutil.which('reframe')

args = parseArgs()


""" --- Export some needed ENV_VARS --- """

workdir = os.getcwd()
os.environ['WORKDIR'] = workdir
os.environ['HOSTNAME'] = args.machine
home = os.getenv('HOME')

os.environ['RFM_TEST_DIR'] = os.path.join(workdir, 'src/feelpp/benchmarking/reframe/regression-tests')

os.environ['FEELPPDB_PATH'] = '/data/scratch/pierre/feelppdb'


#print("\n[BOUCLE START]")
counter = 0
rfmPrefix = os.getenv('RFM_PREFIX')

for meshIndex in ['M2']:    #, 'M3', 'M4']:
    os.environ['MESH_INDEX'] = meshIndex

    for solverType in ['simple', 'lsc']:
        os.environ['SOLVER_TYPE'] = solverType
        os.environ['RFM_PREFIX'] = os.path.join(workdir, 'build/reframe', solverType + f'-{meshIndex}')

        for toolbox in args.toolboxes:
            os.environ['TOOLBOX'] = toolbox

            for mode in args.mode:
                
                print(f" > [ SOLVER_TYPE = {solverType} ]")
                print(f" > [ MESH_INDEX = {meshIndex} ]")

                counter += 1

                cmd = [ f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/reframeConfig.py',
                        f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/{args.machine}.py',
                        f'--mode={mode}',
                        f'--system={args.machine}',     # --report_file (see below)       
                        f'--report-file={workdir}/build/runReports/{toolbox}/Eye-{solverType}-{meshIndex}.json',
                        '--keep-stage-files' ]

                str_cmd = ' '.join(['reframe'] + cmd)
                if args.list:
                    str_cmd += ' -l'

                #print('\t > cmd:', cmd)
                #print("\n[STR_CMD]")
                #print(str_cmd, "\n")

                os.system(str_cmd)
                print('=' * shutil.get_terminal_size().columns)


print("\n > Number of tests run:\t", counter)
print()
# "--report_file=${PWD}/docs/modules/${HOSTNAME}/pages/reports/${tb}/${relative_dir}/${current_date}-${base_name}.json"