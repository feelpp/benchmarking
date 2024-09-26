import os
import sys
import json
import glob
import shutil
from jsonschema                         import validate, ValidationError
from datetime                           import datetime
from feelpp.benchmarking.feelpp_toolboxes.parser         import parseArgs, printArgs
from feelpp.benchmarking.feelpp_toolboxes.config.configReader   import supported_env_vars
from feelpp.benchmarking.report.handlers import GirderHandler


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
    schema_path = f'{parent_folder}/config/configSchema.json'

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
        prefix = f'{parent_folder}/toolboxes_reframe_reports/{toolbox}/{hostname}/'

    if suffix == '' or suffix == 'default':
        configName = os.path.basename(configPath)
        suffix = f'{date}-{configName}'

    reportPath = prefix + suffix
    return reportPath


def buildMapToExport(configPath, hostname):
    varMap = {}
    varMap['CONFIG_PATH'] = configPath

    with open(configPath, 'r') as file:
        data = json.load(file)

    toolbox = data['feelpp']['toolbox']
    varMap['TOOLBOX'] = toolbox
    varMap['RFM_PREFIX'] = data['reframe']['directories']['prefix']
    varMap['RFM_STAGE_DIR'] = data['reframe']['directories']['stage']
    varMap['RFM_OUTPUT_DIR'] = data['reframe']['directories']['output']

    prefix = data['reframe']['report_prefix'].strip()
    suffix = data['reframe']['report_suffix'].strip()
    varMap['RFM_REPORT_FILE'] = buildReportPath(configPath, prefix, suffix, toolbox, hostname)

    varMap['GIRDER_FOLDER_ID'] = data['reframe']['directories']['girder_folder_id']

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

            os.environ["EXEC_POLICY"] = args.policy

            # --report-file option replaced in favour of 'RFM_REPORT_FILE' environment variable
            cmd = [ f'-C {parent_folder}/reframe/config-files/{args.hostname}.py',
                    f'-c {parent_folder}/reframe/regression-tests/cpuVariation.py',
                    f'--system={args.hostname}',
                    f'--exec-policy={args.policy}']    #async/serial

            cmd += ['-l'] if args.list else ['-r']
            if args.verbose:
                cmd += ['-' + 'v' * args.verbose]

            os.system(' '.join(['reframe'] + cmd))

            #============ UPLOAD REPORTS TO GIRDER ================#
            girder_handler = GirderHandler(download_base_dir=None)
            girder_handler.uploadFileToFolder(os.environ['RFM_REPORT_FILE'],os.environ['GIRDER_FOLDER_ID'])
            #======================================================#


            print("\n" + '=' * shutil.get_terminal_size().columns)
        print("\n >>> Number of tests run:", len(configs))
