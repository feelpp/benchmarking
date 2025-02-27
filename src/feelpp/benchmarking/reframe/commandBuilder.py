import os
from datetime import datetime
from pathlib import Path


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
        return self.parser.args.custom_rfm_config or f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.machine}.py'

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
            return "--dry-run --exec-policy serial"
        else:
            return "-r"

    def buildJobOptions(self,timeout):
        #TODO: Generalize (only workf for slurm ?)
        options = []
        if timeout:
            options.append(f"-J time={timeout}")
        return " ".join(options)


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
            f"{self.buildJobOptions(timeout)}",
            f'--perflogdir={os.path.join(self.machine_config.reframe_base_dir,"logs")}',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}',
            f'{self.buildExecutionMode()}'
        ]
        return ' '.join(cmd)
