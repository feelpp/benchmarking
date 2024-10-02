import os
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.config.configSchema import MachineConfig

if __name__ == "__main__":
	parser = Parser()
	parser.printArgs()

	machine_config = ConfigReader(parser.args.exec_config,MachineConfig).config

	os.environ['RFM_STAGE_DIR'] = machine_config.reframe_stage
	os.environ['RFM_OUTPUT_DIR'] = machine_config.reframe_output

	os.environ["EXEC_CONFIG_PATH"] = parser.args.exec_config

	for config_filepath in parser.args.config:
		os.environ["JSON_CONFIG_PATH"] = config_filepath

		cmd = [
			'reframe',
			f'-C {machine_config.config_file}',
			f'-c ./src/feelpp/benchmarking/feelpp_toolboxes/reframe/regression-tests/regression.py',
			f'--system={machine_config.hostname}',
			f'--exec-policy={machine_config.execution_policy}',
			'-r',
			f'{"-"+"v"*parser.args.verbose  if parser.args.verbose else ""}'
		]
		os.system(' '.join(cmd))