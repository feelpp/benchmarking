import os, json,subprocess
from datetime import datetime
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import MachineConfig, ConfigFile
from pathlib import Path
from feelpp.benchmarking.report.config.handlers import GirderHandler


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser
        self.current_date = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
        self.report_folder_path = None

    @staticmethod
    def getScriptRootDir():
        return Path(__file__).resolve().parent

    def buildConfigFilePath(self):
        return f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.machine}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getScriptRootDir() / "regression.py"}'

    def createReportFolder(self,executable):
        folder_path = os.path.join(self.machine_config.reports_base_dir,executable,self.machine_config.machine,str(self.current_date))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.report_folder_path = folder_path

        return str(self.report_folder_path)

    def buildCommand(self):
        assert self.report_folder_path is not None, "Report folder path not set"
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'-S machine_config_path={self.parser.args.exec_config}',
            f'-S report_dir_path={str(self.report_folder_path)}',
            f'--system={self.machine_config.machine}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.machine_config.reframe_base_dir}',
            f'--report-file={str(os.path.join(self.report_folder_path,"reframe_report.json"))}',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}',
            '-r',
        ]
        return ' '.join(cmd)


def main_cli():
    parser = Parser()
    parser.printArgs()

    machine_config = ConfigReader(parser.args.exec_config,MachineConfig).config

    #Sets the cachedir and tmpdir directories for containers
    for container in machine_config.containers:
        if container.platform=="apptainer":
            if container.cachedir:
                os.environ["APPTAINER_CACHEDIR"] = container.cachedir
            if container.tmpdir:
                os.environ["APPTAINER_TMPDIR"] = container.cachedir
        elif container.platform=="docker":
            raise NotImplementedError("Docker container directories configuration is not implemented")

    cmd_builder = CommandBuilder(machine_config,parser)

    for config_filepath in parser.args.config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath
        app_config = ConfigReader(config_filepath,ConfigFile).config

        report_folder_path = cmd_builder.createReportFolder(app_config.executable)

        reframe_cmd = cmd_builder.buildCommand()

        if app_config.platform and app_config.platform.type == "apptainer":
            if app_config.platform.image.protocol != "local" :
                # process = subprocess.Popen(f"apptainer pull -F {app_config.platform} {app_config.platform}", shell=True, stdout=subprocess.PIPE) #TODO: handle image location
                # process.wait()
                # if not os.path.exists(app_config.platform.image_download_location):
                #     raise FileExistsError("Image was not downloaded.")
                #TODO: Change config.platform.image.name to download location
                raise NotImplementedError("Image downloading is not implemented yet. Please pull manually and provide the path")

        exit_code = os.system(reframe_cmd)

        #============ CREATING RESULT ITEM ================#
        with open(os.path.join(report_folder_path,"plots.json"),"w") as f:
            f.write(json.dumps([p.model_dump() for p in app_config.plots]))


        if parser.args.move_results:
            if not os.path.exists(parser.args.move_results):
                os.makedirs(parser.args.move_results)
            os.rename(os.path.join(report_folder_path,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
            os.rename(os.path.join(report_folder_path,"plots.json"),os.path.join(parser.args.move_results,"plots.json"))
        #======================================================#

    return exit_code