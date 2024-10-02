import os
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.config.configSchema import MachineConfig


class CommandBuilder:
    def __init__(self, machine_config, parser):
        self.machine_config = machine_config
        self.parser = parser

    def build_command(self):
        cmd = [
            'reframe',
            f'-C {self.machine_config.config_file}',
            f'-c ./src/feelpp/benchmarking/feelpp_toolboxes/reframe/regression.py',
            f'--system={self.machine_config.hostname}',
            f'--exec-policy={self.machine_config.execution_policy}',
            '-r',
            f'{"-"+"v"*self.parser.args.verbose  if self.parser.args.verbose else ""}'
        ]
        return ' '.join(cmd)


if __name__ == "__main__":
	parser = Parser()
	parser.printArgs()

	machine_config = ConfigReader(parser.args.exec_config,MachineConfig).config

	cmd_builder = CommandBuilder(machine_config,parser)

	os.environ['RFM_STAGE_DIR'] = machine_config.reframe_stage
	os.environ['RFM_OUTPUT_DIR'] = machine_config.reframe_output

	os.environ["EXEC_CONFIG_PATH"] = parser.args.exec_config

	for config_filepath in parser.args.config:
		os.environ["JSON_CONFIG_PATH"] = config_filepath

		reframe_cmd = cmd_builder.build_command()

		os.system(reframe_cmd)