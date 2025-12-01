import os, sys, glob
from feelpp.benchmarking.argsParser import BaseParser

class Parser(BaseParser):
    """ Class for parsing and validating command-line arguments"""
    def __init__(self,print_args=True):
        super().__init__(print_args,"Execute a benchmark")

    def processArgs(self):
        """ Pipeline to process arguments. Will:
            - check that directories exist
            - building a configuration file list
        """
        self.convertPathsToAbsolute()

    def addArgs(self):
        """ Add the necessary arguments to the parser"""
        options = self.parser.add_argument_group("Options")
        options.add_argument('--machine-config', '-mc', required=True, type=str, metavar='MACHINE_CONFIG', help='Path to JSON reframe machine configuration file, specific to a system.')
        options.add_argument('--plots-config', '-pc', required=False, default=None, type=str, help='Path to JSON plots configuration file, used to generate figures. \nIf not provided, no plots will be generated. The plots configuration can also be included in the benchmark configuration file, under the "plots" field.')
        options.add_argument('--benchmark-config', '-bc', type=str, required=True, metavar='CONFIG', help='Paths to JSON benchmark configuration file.')
        options.add_argument('--custom-rfm-config', '-rc', type=str, required=False, default=None, help="Additional reframe configuration file to use instead of built-in ones. It should correspond the with the --machine-config specifications.")
        options.add_argument('--move-results', "-mv", type=str, help='Directory to move the resulting files to. \nIf not provided, result files will be located under the directory specified by the machine configuration.', required=False, default=None)
        options.add_argument('--verbose', '-v', action='count', default=0, help='Select verbose level by specifying multiple v\'s. ')
        options.add_argument('--website', '-w', action='store_true', help='Render reports, compile them and create the website.')
        options.add_argument('--dry-run', action='store_true', help='Execute ReFrame in dry-run mode. No tests will run, but the script to execute it will be generated in the stage directory. Config validation will be skipped, although warnings will be raised if bad.')

        self.parser.add_argument('--reframe-args', '-rfm', type=str, nargs="?", default="", help='Arguments for ReFrame')


    def convertPathsToAbsolute(self):
        """ Converts arguments that contain paths to absolute. No change is made if absolute paths are provided"""
        self.args.benchmark_config = os.path.abspath(self.args.benchmark_config)
        self.args.machine_config = os.path.abspath(self.args.machine_config)

        if self.args.plots_config:
            self.args.plots_config = os.path.abspath(self.args.plots_config)

        if self.args.custom_rfm_config:
            self.args.custom_rfm_config = os.path.abspath(self.args.custom_rfm_config)

        if self.args.move_results:
            self.args.move_results = os.path.abspath(self.args.move_results)

    def validate(self):
        if self.args.custom_rfm_config:
            if not os.path.isfile(self.args.custom_rfm_config):
                self.parser.error(f"Provided custom reframe configuration file {self.args.custom_rfm_config} not found...")

        if not os.path.isfile(self.args.benchmark_config):
            self.parser.error(f"Benchmark configuration file {self.args.benchmark_config} cannot be found")

        if not os.path.isfile(self.args.machine_config):
            self.parser.error(f"Machine configuration file {self.args.machine_config} cannot be found")

        if self.args.plots_config:
            if not os.path.isfile(self.args.plots_config):
                self.parser.error(f"Plot configuration file {self.args.plots_config} cannot be found")