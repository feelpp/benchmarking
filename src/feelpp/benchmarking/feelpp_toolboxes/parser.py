import os
import sys
import glob
import shutil
import json
from jsonschema import validate, ValidationError
from argparse import ArgumentParser, RawTextHelpFormatter


class CustomHelpFormatter(RawTextHelpFormatter):
    """
    Disables 'nargs' and 'choices' special formatting:
        * in usage:         - removes ARG [ARG ...] for nargs
        * in option_group:  - removes ARG [ARG ...] for nargs
                            - removes {choice1, choice2, ...} for choices
    """

    def _format_action_invocation(self, action):
        if action.option_strings:
            return ', '.join(action.option_strings)
        else:
            return super()._format_action_invocation(action)


    def _format_usage(self, usage, actions, groups, prefix):
        """ Removes ARG [ARG ...] for nargs """
        print("")
        usage = f"Usage: {self._prog} "
        usageArgs = []

        for action in actions:
            # Options
            if action.option_strings:
                if action.choices:
                    choicesTxt = ','.join(action.choices)
                    usageArgs.append(f"[{action.option_strings[0]} {{{choicesTxt}}}]")
                elif action.nargs:
                    usageArgs.append(f"[{action.option_strings[0]} {action.metavar} ...]")
                elif action.required:
                    usageArgs.append(f"{action.option_strings[0]} {action.metavar}")
                elif action.metavar != None:
                    usageArgs.append(f"[{action.option_strings[0]} {action.metavar}]")
                else:
                    usageArgs.append(f"[{action.option_strings[0]}]")

            # Positional arguments
            else:
                usageArgs.append(f"{action.dest.upper()}")

        return usage + ' '.join(usageArgs) + "\n"


class Parser():

    def __init__(self):
        self.parser = ArgumentParser(formatter_class=CustomHelpFormatter, add_help=False)
        self.valid_hostnames = ['gaya', 'local', 'discoverer', 'karolina', 'meluxina']
        self.addArgs()
        self.args = self.parser.parse_args()
        self.processArgs()
        if self.args.list_files:
            self.listFilesAndExit()

    def processArgs(self):
        self.validateOptions()
        if self.args.dir:
            self.checkDirectoriesExist()
        self.buildConfigList()
        self.validateConfigs()

    def addArgs(self):
        positional = self.parser.add_argument_group("Positional arguments")
        positional.add_argument('hostname', type=str, choices=self.valid_hostnames, help='Name of the machine \nValid choices: {%(choices)s}', metavar='hostname')

        options = self.parser.add_argument_group("Options")
        options.add_argument('--feelppdb', '-f', type=str, required=True, metavar='PATH', help='Path to feelppdb folder (required)')
        #options.add_argument('--report-prefix', '-r', type=str, nargs='+', metavar='REPORT', help='Prefix for Reframe\'s run-report path \nSuffixe is always: \'{date}-{configBasename}.json\'')
        options.add_argument('--config', '-c', type=str, nargs='+', action='extend', default=[], metavar='CONFIG', help='Paths to JSON configuration files \nIn combination with --dir, specify only basenames for selecting JSON files')
        options.add_argument('--dir', '-d', type=str, nargs='+', action='extend', default=[], metavar='DIR', help='Name of the directory containing JSON configuration files')
        options.add_argument('--exclude', '-e', type=str, nargs='+', action='extend', default=[], metavar='EXCLUDE', help='To use in combination with --dir, mentioned files will not be launched')
        options.add_argument('--policy', '-p', type=str, choices=['async', 'serial'], default='serial', metavar='POLICY', help='Reframe\'s execution policy: {%(choices)s} (default: serial)')
        options.add_argument('--list', '-l', action='store_true', help='List all parametrized tests that will be run by Reframe')
        options.add_argument('--list-files', '-lf', action='store_true', help='List all benchmarking configuration file found')
        options.add_argument('--verbose', '-v', action='count', default=0, help='Select Reframe\'s verbose level by specifying multiple v\'s')
        options.add_argument('--help', '-h', action='help', help='Display help and quit program')

    def validateOptions(self):
        if not self.args.config and not self.args.dir:
            print(f'[Error] At least one of --config or --dir option must be specified')
            sys.exit(1)

        if self.args.config and len(self.args.dir) > 1:
            print(f'[Error] --dir and --config combination can only handle one DIR')
            sys.exit(1)

    def checkDirectoriesExist(self):
        not_found = []
        for dir in self.args.dir:
            if not os.path.isdir(dir):
                not_found.append(dir)

        if not_found:
            print(f'[Error] Following directories were not found')
            for dir in not_found:
                print(f" > {dir}")
            sys.exit(1)

    def buildConfigList(self):
        configs = []
        if self.args.dir:
            for dir in self.args.dir:
                path = os.path.join(dir, '**/*.json')
                json_files = glob.glob(path, recursive=True)
                configs.extend(json_files)
            if self.args.config:
                configs = [config for config in configs if os.path.basename(config) in self.args.config]

        if self.args.config and not self.args.dir:
            configs = self.args.config

        if self.args.exclude:
            configs = [config for config in configs if os.path.basename(config) not in self.args.exclude]

        self.args.config = [os.path.abspath(config) for config in configs]


    def validateConfigs(self):
        parent_folder = os.path.abspath(os.path.dirname(__file__))
        schema_path = f'{parent_folder}/config/configSchema.json'

        with open(schema_path, 'r') as file:
            schema = json.load(file)

        unvalid = []
        messages = []
        for config in self.args.config:
            instance = None
            try:
                with open(config, 'r') as file:
                    instance = json.load(file)
            except FileNotFoundError as e:
                unvalid.append(config)
                messages.append(f"File not found: {e.strerror}")
            except json.JSONDecodeError as e:
                unvalid.append(config)
                messages.append(f"Invalid JSON format: {e.msg}")

            if instance:
                try:
                    validate(instance=instance, schema=schema)
                except ValidationError as e:
                    unvalid.append(config)
                    messages.append(f"Validation error: {e.message}")

        if unvalid:
            print("\n[Error] Corrupted configuration files. Please check before relaunch or use --exclude option.")
            for i in range(len(unvalid)):
                print(f"> file {i+1}:", unvalid[i])
                print(f"\t  {messages[i]}")
            sys.exit(1)

    def listFilesAndExit(self):
        print("\nFollowing configuration files have been found and validated:")
        for config_path in self.args.config:
            print(f"\t> {config_path}")
        print(f"\nTotal: {len(self.args.config)} file(s)")
        sys.exit(0)

    def printArgs(self):
        print("\n[Loaded command-line options]")
        for arg in vars(self.args):
            print(f"\t > {arg + ':' :<{20}} {getattr(self.args, arg)}")
        print("\n" + '=' * shutil.get_terminal_size().columns)