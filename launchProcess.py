import os
import json
import glob
from jsonschema                                         import validate, ValidationError
from datetime                                           import datetime
from src.feelpp.benchmarking.parser                     import *
from src.feelpp.benchmarking.configReader               import supportedEnvVars


def getDate(format="%Y%m%d"):
    date = datetime.now()
    return date.strftime(format)


def buildConfigList(args):
    configLst = []

    if args.dir:
        for dir in args.dir:
            path = os.path.join(dir, '**/*.json')
            jsonFiles = glob.glob(path, recursive=True)

            for file in jsonFiles:
                basename = os.path.basename(file)
                if args.exclude and basename in args.exclude:
                    continue
                if args.config and basename not in args.config:
                    continue
                configLst.append(file)

    elif args.config:
        configLst = args.config

    return [os.path.abspath(config) for config in configLst]


def validateConfigs(configs):

    schemaPath = f'{os.getcwd()}/src/feelpp/benchmarking/configSchema.json'

    with open(schemaPath, 'r') as file:
        schema = json.load(file)

    unvalid = []
    messages = []
    for config in configs:
        try:
            with open(config, 'r') as file:
                instance = json.load(file)
            validate(instance=instance, schema=schema)

        except ValidationError as e:
            unvalid.append(config)
            messages.append(e.message)

        except json.JSONDecodeError as e:
            unvalid.append(config)
            messages.append(e.message)

    if unvalid:
        print("\n[Error] Corrupted configuration files. Please check before relaunch or use --exclude option.")
        for i in range(len(unvalid)):
            print(f"> file {i+1}:", unvalid[i])
            print(f"\t {messages[i]}")
        sys.exit(1)


def globalVarExporter(hostname, feelppdbPath):
    os.environ['WORKDIR'] = os.getcwd()
    os.environ['HOSTNAME'] = hostname
    os.environ['FEELPPDB_PATH'] = feelppdbPath


# Issue adressed to Reframe Dev-Team for manipulating report-path from within a test
def buildReportPath(configPath, prefix, suffix, toolbox):

    if prefix == '' or prefix == 'default':
        prefix = f'{os.getcwd()}/toolboxes_reframe_reports/{toolbox}/{args.hostname}/'

    if suffix == '' or suffix == 'default':
        configName = os.path.basename(configPath)
        suffix = f'{getDate()}-{configName}'

    reportPath = prefix + suffix
    return reportPath


def buildMapToExport(configPath):
    varMap = {}
    varMap['CONFIG_PATH'] = configPath

    with open(configPath, 'r') as file:
        data = json.load(file)

    toolbox = data['Feelpp']['toolbox']
    varMap['TOOLBOX'] = toolbox
    varMap['RFM_PREFIX'] = data['Reframe']['Directories']['prefix']
    varMap['RFM_STAGE_DIR'] = data['Reframe']['Directories']['stage']
    varMap['RFM_OUTPUT_DIR'] = data['Reframe']['Directories']['output']

    prefix = data['Reframe']['reportPrefix'].strip()
    suffix = data['Reframe']['reportSuffix'].strip()
    varMap['RFM_REPORT_FILE'] = buildReportPath(configPath, prefix, suffix, toolbox)

    return varMap


def processEnvVars(value):
    for var in supportedEnvVars:
        if var in value:
            value = value.replace(f'${{{var}}}', os.environ[f'{var}'])
    return value


def configVarExporter(configPath):
    for key, value in buildMapToExport(configPath).items():
        value = value.strip()
        if value != '':
            os.environ[key] = processEnvVars(value)



# +------------------------------------+
# |              MAIN                  |
# +------------------------------------+


if __name__ == '__main__':

    workdir = os.getcwd()

    args = parseArgs()
    printArgs(args)

    configs = buildConfigList(args)
    validateConfigs(configs)

    if args.list_files:
        print("\nFollowing configuration files have been found and validated:")
        for configPath in configs:
            print(f"\t> {configPath}")
        print(f"\nTotal: {len(configs)} file(s)")

    else:
        globalVarExporter(args.hostname, args.feelppdb)
        for configPath in configs:

            configVarExporter(configPath)
            print(f"[{os.environ['TOOLBOX'].upper()} - {os.path.basename(configPath)}]")

            os.environ["EXEC_POLICY"] = args.policy

            # --report-file option replaced in favour of 'RFM_REPORT_FILE' environment variable
            cmd = [ f'-C {workdir}/src/feelpp/benchmarking/reframe/config-files/{args.hostname}.py',
                    f'-c {workdir}/src/feelpp/benchmarking/reframe/regression-tests/cpuVariation.py',
                    f'--system={args.hostname}',
                    f'--exec-policy={args.policy}']    #async/serial

            cmd += ['-l'] if args.list else ['-r']
            if args.verbose:
                cmd += ['-' + 'v' * args.verbose]

            os.system(' '.join(['reframe'] + cmd))
            print("\n" + '=' * shutil.get_terminal_size().columns)
        print("\n >>> Number of tests run:", len(configs))
