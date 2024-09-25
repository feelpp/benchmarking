import os
import sys
import json
import glob
import shutil
from jsonschema                         import validate, ValidationError
from datetime                           import datetime
from feelpp.benchmarking.parser         import parseArgs, printArgs
from feelpp.benchmarking.configReader   import supported_env_vars


def getParentFolder():
    return os.path.abspath(os.path.dirname(__file__))


def buildConfigList(args):
    configs = []

    if args.dir:
        for dir in args.dir:
            path = os.path.join(dir, '**/*.json')
            json_files = glob.glob(path, recursive=True)

            for file in json_files:
                basename = os.path.basename(file)
                if args.exclude and basename in args.exclude:
                    continue
                if args.config and basename not in args.config:
                    continue
                configs.append(file)

    elif args.config:
        configs = args.config

    return [os.path.abspath(config) for config in configs]


def validateConfigs(configs):
    parent_folder = getParentFolder()
    schema_path = f'{parent_folder}/src/feelpp/benchmarking/configSchema.json'

    with open(schema_path, 'r') as file:
        schema = json.load(file)

    unvalid = []
    messages = []
    instance = None
    for config in configs:
        try:
            with open(config, 'r') as file:
                instance = json.load(file)
        except json.JSONDecodeError as e:
            unvalid.append(config)
            messages.append(f"Invalid JSON format: {e.msg}")

        if instance:
            try:
                validate(instance=instance, schema=schema)
            except ValidationError as e:
                unvalid.append(config)
                messages.append(f"Validation error: {e.message}")

    if unvalid:
        print("\n[Error] Corrupted configuration files. Please check before relaunch or use --exclude option.")
        for i in range(len(unvalid)):
            print(f"> file {i+1}:", unvalid[i])
            print(f"\t  {messages[i]}")
        sys.exit(1)


def globalVarExporter(hostname, feelppdbPath):
    os.environ['WORKDIR'] = getParentFolder()
    os.environ['HOSTNAME'] = hostname
    os.environ['FEELPPDB_PATH'] = feelppdbPath


def buildReportPath(configPath, prefix, suffix, toolbox, hostname, format="%Y%m%dT%H%M%S"):
    date = datetime.now().strftime(format)
    parent_folder = getParentFolder()

    if prefix == '' or prefix == 'default':
        prefix = f'{parent_folder}/docs/modules/{hostname}/pages/reports/'

    if suffix == '' or suffix == 'default':
        configName = os.path.basename(configPath)
        suffix = f'{toolbox}/{date}-{configName}'

    reportPath = prefix + suffix
    return reportPath


def buildMapToExport(configPath, hostname):
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
    varMap['RFM_REPORT_FILE'] = buildReportPath(configPath, prefix, suffix, toolbox, hostname)

    return varMap


def processEnvVars(value):
    for var in supported_env_vars:
        if var in value:
            value = value.replace(f'${{{var}}}', os.environ[f'{var}'])
    return value


def configVarExporter(configPath, hostname):
    for key, value in buildMapToExport(configPath, hostname).items():
        value = value.strip()
        if value != '':
            os.environ[key] = processEnvVars(value)


def launchReframe():
    parent_folder = getParentFolder()
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

            configVarExporter(configPath, args.hostname)
            print(f"[{os.environ['TOOLBOX'].upper()} - {os.path.basename(configPath)}]")

            # --report-file option replaced in favour of 'RFM_REPORT_FILE' environment variable
            cmd = [ f'-C {parent_folder}/src/feelpp/benchmarking/reframe/config-files/{args.hostname}.py',
                    f'-c {parent_folder}/src/feelpp/benchmarking/reframe/regression-tests/cpuVariation.py',
                    f'--system={args.hostname}',
                    f'--exec-policy={args.policy}']    #async/serial

            cmd += ['-l'] if args.list else ['-r']
            if args.verbose:
                cmd += ['-' + 'v' * args.verbose]

            os.system(' '.join(['reframe'] + cmd))
            print("\n" + '=' * shutil.get_terminal_size().columns)
        print("\n >>> Number of tests run:", len(configs))



if __name__ == '__main__':
    launchReframe()