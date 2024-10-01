import os, argparse
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    positional = parser.add_argument_group("Positional arguments")
    positional.add_argument('hostname', type=str, choices=['gaya'], help='Name of the machine \nValid choices: {%(choices)s}', metavar='hostname')

    options = parser.add_argument_group("Options")
    options.add_argument('--config', '-c', type=str)
    options.add_argument('--policy', '-p', type=str, choices=['async', 'serial'], default='serial', metavar='POLICY', help='Reframe\'s execution policy: {%(choices)s} (default: serial)')

    args = parser.parse_args()

    os.environ["JSON_CONFIG_PATH"] = args.config

    cmd = [ 'reframe',
            f'-C ./src/feelpp/benchmarking/feelpp_toolboxes/config/config-files/{args.hostname}.py',
            f'-c ./src/feelpp/benchmarking/feelpp_toolboxes/reframe/regression-tests/regression.py',
            f'--system={args.hostname}',
            f'--exec-policy={args.policy}',
            '-r','-v']

    os.system(' '.join(cmd))