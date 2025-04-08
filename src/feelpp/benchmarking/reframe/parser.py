import os
import sys
import glob
import shutil
from argparse import ArgumentParser, RawTextHelpFormatter, REMAINDER


class CustomHelpFormatter(RawTextHelpFormatter):
    """
    Class for formatting the usage and the options display of the parser
    """
    def _format_action_invocation(self, action):
        """ Override of RawTextHelpFormatter method
        Removes ARG [ARG ...] for nargs and {choice1, choice2, ...} in option_group
        """
        if action.option_strings:
            return ', '.join(action.option_strings)
        else:
            return super()._format_action_invocation(action)

    def _format_usage(self, usage, actions, groups, prefix):
        """ Override of RawTextHelpFormatter method
        Removes ARG [ARG ...] for nargs in usage
        """
        print("")
        usage = f"Usage: {self._prog} "
        usage_args = []

        for action in actions:
            # Options
            if action.option_strings:
                if action.choices:
                    choices_str = ','.join(action.choices)
                    usage_args.append(f"[{action.option_strings[0]} {{{choices_str}}}]")
                elif action.nargs:
                    usage_args.append(f"[{action.option_strings[0]} {action.metavar} ...]")
                elif action.required:
                    usage_args.append(f"{action.option_strings[0]} {action.metavar}")
                elif action.metavar != None:
                    usage_args.append(f"[{action.option_strings[0]} {action.metavar}]")
                else:
                    usage_args.append(f"[{action.option_strings[0]}]")

            # Positional arguments
            else:
                usage_args.append(f"{action.dest.upper()}")

        return usage + ' '.join(usage_args) + "\n"


class Parser():
    """ Class for parsing and validating command-line arguments"""
    def __init__(self):
        self.parser = ArgumentParser(formatter_class=CustomHelpFormatter, add_help=False)
        self.addArgs()
        self.args = self.parser.parse_args()
        self.processArgs()
        if self.args.list_files:
            self.listFilesAndExit()

    def processArgs(self):
        """ Pipeline to process arguments. Will:
            - validate the options
            - check that directories exist
            - building a configuration file list
        """
        self.validateOptions()
        if self.args.dir:
            self.checkDirectoriesExist()
        self.buildConfigList()
        self.convertPathsToAbsolute()

    def addArgs(self):
        """ Add the necessary arguments to the parser"""
        options = self.parser.add_argument_group("Options")
        options.add_argument('--machine-config', '-mc', required=True, type=str, metavar='MACHINE_CONFIG', help='Path to JSON reframe machine configuration file, specific to a system.')
        options.add_argument('--plots-config', '-pc', required=False, default=None, type=str, help='Path to JSON plots configuration file, used to generate figures. \nIf not provided, no plots will be generated. The plots configuration can also be included in the benchmark configuration file, under the "plots" field.')
        options.add_argument('--benchmark-config', '-bc', type=str, nargs='+', action='extend', default=[], metavar='CONFIG', help='Paths to JSON benchmark configuration files \nIn combination with --dir, specify only provide basenames for selecting JSON files.')
        options.add_argument('--custom-rfm-config', '-rc', type=str, required=False, default=None, help="Additional reframe configuration file to use instead of built-in ones. It should correspond the with the --machine-config specifications.")
        options.add_argument('--dir', '-d', type=str, nargs='+', action='extend', default=[], metavar='DIR', help='Name of the directory containing JSON configuration files')
        options.add_argument('--exclude', '-e', type=str, nargs='+', action='extend', default=[], metavar='EXCLUDE', help='To use in combination with --dir, mentioned files will not be launched. \nOnly provide basenames to exclude.')
        options.add_argument('--move-results', "-mv", type=str, help='Directory to move the resulting files to. \nIf not provided, result files will be located under the directory specified by the machine configuration.', required=False, default=None)
        options.add_argument('--list-files', '-lf', action='store_true', help='List all benchmarking configuration file found. \nIf this option is provided, the application will not run. Use it for validation.')
        options.add_argument('--verbose', '-v', action='count', default=0, help='Select Reframe\'s verbose level by specifying multiple v\'s. ')
        options.add_argument('--help', '-h', action='help', help='Display help and quit program')
        options.add_argument('--website', '-w', action='store_true', help='Render reports, compile them and create the website.')
        options.add_argument('--dry-run', action='store_true', help='Execute ReFrame in dry-run mode. No tests will run, but the script to execute it will be generated in the stage directory. Config validation will be skipped, although warnings will be raised if bad.')

        self.parser.add_argument('--reframe-args', '-rfm', type=str, nargs="?", default="", help='Arguments for ReFrame')


    def convertPathsToAbsolute(self):
        """ Converts arguments that contain paths to absolute. No change is made if absolute paths are provided"""
        self.args.benchmark_config = [os.path.abspath(c) for c in self.args.benchmark_config]
        self.args.machine_config = os.path.abspath(self.args.machine_config)
        if self.args.plots_config:
            self.args.plots_config = os.path.abspath(self.args.plots_config)

    def validateOptions(self):
        """ Checks that required args are present, and that they latch the expected format"""
        if not self.args.benchmark_config and not self.args.dir:
            print(f'[Error] At least one of --benchmark-config or --dir option must be specified')
            sys.exit(1)

        if self.args.benchmark_config and len(self.args.dir) > 1:
            print(f'[Error] --dir and --benchmark-config combination can only handle one DIR')
            sys.exit(1)

        if not self.args.machine_config:
            print(f'[Error] --machine-config should be specified')
            sys.exit(1)



    def checkDirectoriesExist(self):
        """ Check that directories passed as arguments exist in the filesystem"""
        not_found = []
        for dir in self.args.dir:
            if not os.path.isdir(dir):
                not_found.append(dir)

        if not_found:
            print(f'[Error] Following directories were not found')
            for dir in not_found:
                print(f" > {dir}")
            sys.exit(1)

        if self.args.custom_rfm_config:
            if not os.path.isfile(self.args.custom_rfm_config):
                print(f"Provided custom reframe configuration file {self.args.custom_rfm_config} not found...")
                sys.exit(1)

    def buildConfigList(self):
        """ Find configuration filepaths specified by the --dir argument and build a list acordingly.
        If --benchmark_config is passed, then a list with a single config filepath is set"""
        configs = []
        if self.args.dir:
            for dir in self.args.dir:
                path = os.path.join(dir, '**/*.json')
                json_files = glob.glob(path, recursive=True)
                configs.extend(json_files)
            if self.args.benchmark_config:
                configs = [config for config in configs if os.path.basename(config) in self.args.benchmark_config]

        if self.args.benchmark_config and not self.args.dir:
            configs = self.args.benchmark_config

        if self.args.exclude:
            configs = [config for config in configs if os.path.basename(config) not in self.args.exclude]

        self.args.benchmark_config = [os.path.abspath(config) for config in configs]

    def listFilesAndExit(self):
        """ Print configuration filepaths and exits"""
        print("\nFollowing configuration files have been found and validated:")
        for config_path in self.args.benchmark_config:
            print(f"\t> {config_path}")
        print(f"\nTotal: {len(self.args.benchmark_config)} file(s)")
        sys.exit(0)

    def printArgs(self):
        """ Prints arguments on the standard output"""
        print("\n[Loaded command-line options]")
        for arg in vars(self.args):
            print(f"\t > {arg + ':' :<{20}} {getattr(self.args, arg)}")
        print("\n" + '=' * shutil.get_terminal_size().columns)