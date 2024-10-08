import os
from datetime import datetime
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import MachineConfig, ConfigFile
from pathlib import Path
from feelpp.benchmarking.report.handlers import GirderHandler
import json


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser
        self.current_date = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")

    @staticmethod
    def getScriptRootDir():
        return Path(__file__).resolve().parent

    def buildConfigFilePath(self):
        return f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.hostname}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getScriptRootDir() / "regression.py"}'

    def buildReportFilePath(self,executable):
        return str(os.path.join(self.machine_config.reports_base_dir,executable,self.machine_config.hostname,f"{self.current_date}.json"))

    def build_command(self,executable):
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'-S machine_config_path={self.parser.args.exec_config}',
            f'--system={self.machine_config.hostname}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.machine_config.reframe_base_dir}',
            f'--report-file={self.buildReportFilePath(executable)}',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}',
            '-r',
        ]
        return ' '.join(cmd)


def main_cli():
    parser = Parser()
    parser.printArgs()

    machine_config = ConfigReader(parser.args.exec_config,MachineConfig).config

    cmd_builder = CommandBuilder(machine_config,parser)

    for config_filepath in parser.args.config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath
        app_config = ConfigReader(config_filepath,ConfigFile).config
        reframe_cmd = cmd_builder.build_command(app_config.executable)
        os.system(reframe_cmd)

        #============ UPLOAD REPORTS TO GIRDER ================#
        if app_config.upload.active:
            match app_config.upload.platform:
                case "girder":
                    girder_handler = GirderHandler(download_base_dir=None)
                    rfm_report_filepath = cmd_builder.buildReportFilePath(app_config.executable)

                    #Upload reframe report
                    girder_handler.uploadFileToFolder(
                        rfm_report_filepath,
                        app_config.upload.folder_id
                    )
                    #Upload plots data
                    girder_handler.uploadStringToItem(
                        json.dumps([p.model_dump() for p in app_config.plots]),
                        rfm_report_filepath.split("/")[-1].replace(".json","_plots.json"),
                        girder_handler.item_id, #Can cause bugs because of async?
                        parent_type="item"
                    )
                case _:
                    raise NotImplementedError
        #======================================================#


if __name__ == "__main__":
    main_cli()