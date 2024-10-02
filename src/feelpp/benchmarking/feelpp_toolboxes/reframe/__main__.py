import os
from feelpp.benchmarking.feelpp_toolboxes.parser import Parser

if __name__ == "__main__":
	parser = Parser()
	parser.printArgs()

	for config_filepath in parser.args.config:
		os.environ["JSON_CONFIG_PATH"] = config_filepath

		cmd = [ 'reframe',
				f'-C ./src/feelpp/benchmarking/feelpp_toolboxes/config/config-files/{parser.args.hostname}.py',
				f'-c ./src/feelpp/benchmarking/feelpp_toolboxes/reframe/regression-tests/regression.py',
				f'--system={parser.args.hostname}',
				f'--exec-policy={parser.args.policy}',
				'-r','-v' ]

		os.system(' '.join(cmd))