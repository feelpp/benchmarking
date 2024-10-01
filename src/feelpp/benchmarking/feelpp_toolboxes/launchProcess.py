import os
import json
import shutil
from datetime import datetime
from feelpp.benchmarking.report.handlers import GirderHandler
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import supported_env_vars


def getParentFolder():
    return os.path.abspath(os.path.dirname(__file__))

def globalVarExporter(hostname, feelppdb_path, policy):
    os.environ['WORKDIR'] = getParentFolder()
    os.environ['HOSTNAME'] = hostname
    os.environ['FEELPPDB_PATH'] = feelppdb_path
    os.environ['EXEC_POLICY'] = policy

def buildReportPath(config_path, prefix, suffix, toolbox, hostname, format="%Y%m%dT%H%M%S"):
    date = datetime.now().strftime(format)
    parent_folder = getParentFolder()

    if prefix == '' or prefix == 'default':
        prefix = f'{parent_folder}/toolboxes_reframe_reports/{toolbox}/{hostname}/'

    if suffix == '' or suffix == 'default':
        configName = os.path.basename(config_path)
        suffix = f'{date}-{configName}'

    reportPath = prefix + suffix
    return reportPath

def buildMapToExport(config_path, hostname):
    varMap = {}
    varMap['CONFIG_PATH'] = config_path

    with open(config_path, 'r') as file:
        data = json.load(file)

    toolbox = data['feelpp']['toolbox']
    prefix = data['reframe']['report_prefix'].strip()
    suffix = data['reframe']['report_suffix'].strip()

    varMap['TOOLBOX'] = toolbox
    varMap['RFM_PREFIX'] = data['reframe']['directories']['prefix']
    varMap['RFM_STAGE_DIR'] = data['reframe']['directories']['stage']
    varMap['RFM_OUTPUT_DIR'] = data['reframe']['directories']['output']
    varMap['RFM_REPORT_FILE'] = buildReportPath(config_path, prefix, suffix, toolbox, hostname)
    varMap['GIRDER_FOLDER_ID'] = data['reframe']['directories']['girder_folder_id']

    return varMap

def processEnvVars(value):
    for var in supported_env_vars:
        if var in value:
            value = value.replace(f'${{{var}}}', os.environ[f'{var}'])
    return value

def configVarExporter(config_path, hostname):
    for key, value in buildMapToExport(config_path, hostname).items():
        value = value.strip()
        if value != '':
            os.environ[key] = processEnvVars(value)

def buildReframeCommands(args):
    parent_folder = getParentFolder()
    cmd = [
        "reframe"
        f"-C {parent_folder}/reframe/config-files/{args.hostname}.py"
        f"-c {parent_folder}/reframe/regression-tests/cpuVariation.py",
        f"--system={args.hostname}",
        f"--exec-policy={args.policy}" #async/serial
    ]

    cmd += ['-l'] if args.list else ['-r']
    if args.verbose:
        cmd += ['-' + 'v' * args.verbose]
    return cmd


def launchReframe():
    parser = Parser()
    parser.printArgs()

    globalVarExporter(parser.args.hostname, parser.args.feelppdb, parser.args.policy)
    for config in parser.args.config:

        configVarExporter(config, parser.args.hostname)
        print(f"[{os.environ['TOOLBOX'].upper()} - {os.path.basename(config)}]")

        cmd = buildReframeCommands(parser.args)
        os.system(cmd)

        #============ UPLOAD REPORTS TO GIRDER ================#
        girder_handler = GirderHandler(download_base_dir=None)
        girder_handler.uploadFileToFolder(os.environ['RFM_REPORT_FILE'],os.environ['GIRDER_FOLDER_ID'])
        #======================================================#

        print("\n" + '=' * shutil.get_terminal_size().columns)
    print("\n >>> Number of tests run:", len(parser.args.config))