import os, json
from datetime import datetime
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from pathlib import Path
from feelpp.benchmarking.reframe.reporting import WebsiteConfig


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser
        self.current_date = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")

    @staticmethod
    def getScriptRootDir():
        return Path(__file__).resolve().parent

    def buildConfigFilePath(self):
        return f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.machine}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getScriptRootDir() / "regression.py"}'

    def buildReportFilePath(self,executable,use_case):
        return str(os.path.join(self.machine_config.reports_base_dir,executable,use_case,self.machine_config.machine,f"{self.current_date}.json"))

    def buildCommand(self,executable,use_case,timeout):
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'--system={self.machine_config.machine}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.machine_config.reframe_base_dir}',
            f"-J '#SBATCH --time={timeout}'",
            f'--perflogdir={os.path.join(self.machine_config.reframe_base_dir,"logs")}',
            f'--report-file={self.buildReportFilePath(executable,use_case)}',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}',
            '-r',
        ]
        return ' '.join(cmd)


def main_cli():
    parser = Parser()
    parser.printArgs()

    machine_reader = ConfigReader(parser.args.exec_config,MachineConfig)
    machine_reader.updateConfig()

    #Sets the cachedir and tmpdir directories for containers
    for platform, dirs in machine_reader.config.containers.items():
        if platform=="apptainer":
            if dirs.cachedir:
                os.environ["APPTAINER_CACHEDIR"] = dirs.cachedir
            if dirs.tmpdir:
                os.environ["APPTAINER_TMPDIR"] = dirs.cachedir
        elif platform=="docker":
            raise NotImplementedError("Docker container directories configuration is not implemented")

    cmd_builder = CommandBuilder(machine_reader.config,parser)

    os.environ["MACHINE_CONFIG_FILEPATH"] = parser.args.exec_config

    website_config = WebsiteConfig(machine_reader.config.reports_base_dir)

    for config_filepath in parser.args.config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath

        configs = [config_filepath]
        if parser.args.plots_config:
            configs += [parser.args.plots_config]
        app_reader = ConfigReader(configs,ConfigFile)
        app_reader.updateConfig(machine_reader.processor.flattenDict(machine_reader.config,"machine"))
        app_reader.updateConfig() #Update with own field

        executable_name = os.path.basename(app_reader.config.executable).split(".")[0]
        reframe_cmd = cmd_builder.buildCommand(executable_name,app_reader.config.use_case_name, app_reader.config.timeout)

        exit_code = os.system(reframe_cmd)

        #============ CREATING RESULT ITEM ================#
        rfm_report_filepath = cmd_builder.buildReportFilePath(executable_name,app_reader.config.use_case_name)
        rfm_report_dir = rfm_report_filepath.replace(".json","")
        os.mkdir(rfm_report_dir)
        os.rename(rfm_report_filepath,os.path.join(rfm_report_dir,"reframe_report.json"))

        with open(os.path.join(rfm_report_dir,"plots.json"),"w") as f:
            f.write(json.dumps([p.model_dump() for p in app_reader.config.plots]))


        if parser.args.move_results:
            if not os.path.exists(parser.args.move_results):
                os.makedirs(parser.args.move_results)
            os.rename(os.path.join(rfm_report_dir,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
            os.rename(os.path.join(rfm_report_dir,"plots.json"),os.path.join(parser.args.move_results,"plots.json"))
        #======================================================#

        #============== UPDATE WEBSITE CONFIG FILE ==============#
        common_itempath = (parser.args.move_results or rfm_report_dir).split("/")
        common_itempath = "/".join(common_itempath[:-1 - (common_itempath[-1] == "")])

        website_config.updateExecutionMapping(
            executable_name, machine_reader.config.machine, app_reader.config.use_case_name,
            report_itempath = common_itempath
        )

        website_config.updateMachine(machine_reader.config.machine)
        website_config.updateUseCase(app_reader.config.use_case_name)
        website_config.updateApplication(executable_name)

        website_config.save()
        #======================================================#

    return exit_code