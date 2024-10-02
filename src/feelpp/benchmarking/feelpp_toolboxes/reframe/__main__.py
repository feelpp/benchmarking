import os
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.config.configSchema import MachineConfig
from pathlib import Path


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser

    @staticmethod
    def getRepositoryRootDir():
        return Path(__file__).resolve().parent.parents[4]

    def buildConfigFilePath(self):
        return f'{self.getRepositoryRootDir() / "src/feelpp/benchmarking/feelpp_toolboxes/config/config-files" / self.machine_config.hostname}.py'

    def buildRegressionTestFilePath(self):
        return f'{self.getRepositoryRootDir() / "src/feelpp/benchmarking/feelpp_toolboxes/reframe/regression.py"}'

    def buildReframePrefixPath(self):
        return f'{self.getRepositoryRootDir() / "build" / "reframe"}'

    def buildReportFilePath(self):
        return f'{self.getRepositoryRootDir() / "reframe_reports" / self.machine_config.hostname / "report-{sessionid}.json"}'

    def build_command(self):
        cmd = [
            'reframe',
            f'-C {self.buildConfigFilePath()}',
            f'-c {self.buildRegressionTestFilePath()}',
            f'--system={self.machine_config.hostname}',
            f'--exec-policy={self.machine_config.execution_policy}',
            f'--prefix={self.buildReframePrefixPath()}',
            f'--report-file={self.buildReportFilePath()}',
            '-r',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}'
        ]
        return ' '.join(cmd)


if __name__ == "__main__":
    parser = Parser()
    parser.printArgs()

    machine_config = ConfigReader(parser.args.exec_config,MachineConfig).config

    cmd_builder = CommandBuilder(machine_config,parser)

    os.environ["EXEC_CONFIG_PATH"] = parser.args.exec_config

    for config_filepath in parser.args.config:
        os.environ["JSON_CONFIG_PATH"] = config_filepath

        reframe_cmd = cmd_builder.build_command()

        os.system(reframe_cmd)