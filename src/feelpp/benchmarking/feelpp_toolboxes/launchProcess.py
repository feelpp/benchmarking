import os
import json
import shutil
from datetime import datetime
from feelpp.benchmarking.report.handlers import GirderHandler
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import supported_env_vars


def getParentFolder():
    """ Return the parent folder of this file """
    return os.path.abspath(os.path.dirname(__file__))

def globalVarExporter(hostname, feelppdb_path, policy):
    """ Export environment variables that are shared by all tests
    Args:
        hostname (str): Name of the current machine
        feelppdb_path (str): Path to the Feel++ root output folder
        policy (str): Reframe's execution policy (async/serial)
    """
    os.environ['WORKDIR'] = getParentFolder()
    os.environ['HOSTNAME'] = hostname
    os.environ['FEELPPDB_PATH'] = feelppdb_path
    os.environ['EXEC_POLICY'] = policy

def buildReportPath(config_path, prefix, suffix, toolbox, hostname, format="%Y%m%dT%H%M%S"):
    """ Build path for ReFrame's JSON run-report
    By default: .../toolboxes_reframe_reports/{toolbox}/{hostname}/{date}-{config_name}.json
    Args:
        config_path (str): The path to the configuration file
        prefix (str): The prefix for the path (specified in JSON configuration file)
        suffix (str): The suffix for the path (specified in JSON configuration file)
        toolbox (str): The name of the Feel++ toolbox
        hostname (str): The name of the current machine
        format (str): The date format
    Returns:
        report_path (str): The path to ReFrame's run-report
    """
    date = datetime.now().strftime(format)
    parent_folder = getParentFolder()

    if prefix == '' or prefix == 'default':
        prefix = f'{parent_folder}/toolboxes_reframe_reports/{toolbox}/{hostname}/'

    if suffix == '' or suffix == 'default':
        config_name = os.path.basename(config_path)
        suffix = f'{date}-{config_name}'

    report_path = prefix + suffix
    return report_path

def buildMapToExport(config_path, hostname):
    """ Build a map of environment variables as key-value pairs for later export
    Use of RFM_REPORT_FILE instead of --report-file for opening JSON only once
    Args:
        config_path (str): Path to the configuration file
        hostname (str): Name of the current machine
    Returns:
        var_map (dict[str,str]): Dictionary containing environment variables and their values
    """
    var_map = {}
    var_map['CONFIG_PATH'] = config_path

    with open(config_path, 'r') as file:
        data = json.load(file)

    toolbox = data['feelpp']['toolbox']
    prefix = data['reframe']['report_prefix'].strip()
    suffix = data['reframe']['report_suffix'].strip()

    var_map['TOOLBOX'] = toolbox
    var_map['RFM_PREFIX'] = data['reframe']['directories']['prefix']
    var_map['RFM_STAGE_DIR'] = data['reframe']['directories']['stage']
    var_map['RFM_OUTPUT_DIR'] = data['reframe']['directories']['output']
    var_map['RFM_REPORT_FILE'] = buildReportPath(config_path, prefix, suffix, toolbox, hostname)
    var_map['GIRDER_FOLDER_ID'] = data['reframe']['directories']['girder_folder_id']

    return var_map

def processEnvVars(value):
    """ Replace supported environment variables in a string by their values
    Args:
        value (str): A string which may contain environment variables
    Returns:
        value (str): The modified string with the variables' value
    """
    for var in supported_env_vars:
        if var in value:
            value = value.replace(f'${{{var}}}', os.environ[f'{var}'])
    return value

def configVarExporter(config_path, hostname):
    """ Build and export case-specific environment variables:
    Args:
        config_path (str): Path to the configuration file
        hostname (str): Name of the current machine
    """
    for key, value in buildMapToExport(config_path, hostname).items():
        value = value.strip()
        if value != '':
            os.environ[key] = processEnvVars(value)

def buildReframeCommands(args):
    """ Build command-line for launching ReFrame
    Args:
        args (argparse.Namespace): Parsed command-line arguments
    Return:
        Single string obtained by concatenation of cmd_list (list[str])
    """
    parent_folder = getParentFolder()

    cmd_list = [
        "reframe"
        f"-C {parent_folder}/config/config-files/{args.hostname}.py"
        f"-c {parent_folder}/reframe/regression-tests/cpuVariation.py",
        f"--system={args.hostname}",
        f"--exec-policy={args.policy}" #
    ]

    cmd_list += ['-l'] if args.list else ['-r']
    if args.verbose:
        cmd_list += ['-' + 'v' * args.verbose]

    return " ".join(cmd_list)

def launchReframe():
    """ Launch ReFrame Feel++ toolbox test after argument parsing and configuration validation.
    Export of shared variables before loop over configuration files.
    For each configuration file, specific variables will be exported, ReFrame will be launched
    and the run-report will be uploaded to Girder
    """
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