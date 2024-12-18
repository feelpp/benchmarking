import os, json, subprocess
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
        self.report_folder_path = None

    @staticmethod
    def getScriptRootDir():
        return Path(__file__).resolve().parent

    def buildConfigFilePath(self):
        return f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.machine}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getScriptRootDir() / "regression.py"}'

    def createReportFolder(self,executable,use_case):
        folder_path = os.path.join(self.machine_config.reports_base_dir,executable,use_case,self.machine_config.machine,str(self.current_date))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.report_folder_path = folder_path

        return str(self.report_folder_path)

    def buildExecutionMode(self):
        """Write the ReFrame execution flag depending on the parser arguments.
            Examples are --dry-run or -r
        """
        if self.parser.args.dry_run:
            return "--dry-run"
        else:
            return "-r"

    def buildCommand(self,timeout):
        assert self.report_folder_path is not None, "Report folder path not set"
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'-S report_dir_path={str(self.report_folder_path)}',
            f'--system={self.machine_config.machine}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.machine_config.reframe_base_dir}',
            f'--report-file={str(os.path.join(self.report_folder_path,"reframe_report.json"))}',
            f"-J '#SBATCH --time={timeout}'",
            f'--perflogdir={os.path.join(self.machine_config.reframe_base_dir,"logs")}',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}',
            f'{self.buildExecutionMode()}'
        ]
        return ' '.join(cmd)


def main_cli():
    parser = Parser()
    parser.printArgs()

    machine_reader = ConfigReader(parser.args.machine_config,MachineConfig,dry_run=parser.args.dry_run)
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

    os.environ["MACHINE_CONFIG_FILEPATH"] = parser.args.machine_config

    website_config = WebsiteConfig(machine_reader.config.reports_base_dir)

    for config_filepath in parser.args.benchmark_config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath


        configs = [config_filepath]
        if parser.args.plots_config:
            configs += [parser.args.plots_config]
        app_reader = ConfigReader(configs,ConfigFile,dry_run=parser.args.dry_run)
        executable_name = os.path.basename(app_reader.config.executable).split(".")[0]
        report_folder_path = cmd_builder.createReportFolder(executable_name,app_reader.config.use_case_name)
        app_reader.updateConfig(machine_reader.processor.flattenDict(machine_reader.config,"machine"))
        app_reader.updateConfig() #Update with own field

        reframe_cmd = cmd_builder.buildCommand( app_reader.config.timeout )

        exit_code = os.system(reframe_cmd)

        #============ CREATING RESULT ITEM ================#
        with open(os.path.join(report_folder_path,"plots.json"),"w") as f:
            f.write(json.dumps([p.model_dump() for p in app_reader.config.plots]))


        if parser.args.move_results:
            if not os.path.exists(parser.args.move_results):
                os.makedirs(parser.args.move_results)
            os.rename(os.path.join(report_folder_path,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
            os.rename(os.path.join(report_folder_path,"plots.json"),os.path.join(parser.args.move_results,"plots.json"))
        #======================================================#

        #============== UPDATE WEBSITE CONFIG FILE ==============#
        common_itempath = (parser.args.move_results or report_folder_path).split("/")
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

    if parser.args.website:
        subprocess.run(["render-benchmarks","--config_file", website_config.config_filepath])
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

    return exit_code