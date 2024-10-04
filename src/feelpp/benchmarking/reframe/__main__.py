import os
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import MachineConfig
from pathlib import Path


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser

    @staticmethod
    def getScriptRootDir():
        return Path(__file__).resolve().parent

    def buildConfigFilePath(self):
        return f'{self.getScriptRootDir() / "config/machineConfigs" / self.machine_config.hostname}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getScriptRootDir() / "regression.py"}'

    def buildReportFilePath(self):
        return f'{os.path.join(self.machine_config.reports_base_dir,self.machine_config.hostname,"report-{sessionid}.json")}'

    def build_command(self):
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'-S machine_config_path={self.parser.args.exec_config}',
            f'--system={self.machine_config.hostname}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.machine_config.reframe_base_dir}',
            f'--report-file={self.buildReportFilePath()}',
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
        reframe_cmd = cmd_builder.build_command()
        os.system(reframe_cmd)


if __name__ == "__main__":
    main_cli()