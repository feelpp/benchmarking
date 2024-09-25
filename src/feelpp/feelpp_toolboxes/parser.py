import os
import sys
import shutil
from argparse import ArgumentParser, RawTextHelpFormatter


# Reframe host config-file missing for:     'discoverer', 'karolina', 'meluxina'
validHostnames = ['gaya', 'local', 'discoverer', 'karolina', 'meluxina']


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



def parseArgs():

    parser = ArgumentParser(formatter_class=CustomHelpFormatter, add_help=False)

    positional = parser.add_argument_group("Positional arguments")
    positional.add_argument('hostname', type=str, choices=validHostnames, help='Name of the machine \nValid choices: {%(choices)s}', metavar='hostname')

    options = parser.add_argument_group("Options")
    options.add_argument('--feelppdb', '-f', type=str, required=True, metavar='PATH', help='Path to feelppdb folder (required)')
    #options.add_argument('--report-prefix', '-r', type=str, metavar='REPORT', help='Prefix for Reframe\'s run-report path \nSuffixe is always: \'{date}-{configBasename}.json\'')
    options.add_argument('--config', '-c', type=str, nargs='+', action='extend', default=[], metavar='CONFIG', help='Paths to JSON configuration files \nIn combination with --dir, specify only basenames for selecting JSON files')
    options.add_argument('--dir', '-d', type=str, nargs='+', action='extend', default=[], metavar='DIR', help='Name of the directory containing JSON configuration files')
    options.add_argument('--exclude', '-e', type=str, nargs='+', action='extend', default=[], metavar='EXCLUDE', help='To use in combination with --dir, mentioned files will not be launched')
    options.add_argument('--policy', '-p', type=str, choices=['async', 'serial'], default='serial', metavar='POLICY', help='Reframe\'s execution policy: {%(choices)s} (default: serial)')
    options.add_argument('--list', '-l', action='store_true', help='List all parametrized tests that will be run by Reframe')
    options.add_argument('--list-files', '-lf', action='store_true', help='List all benchmarking configuration file found')
    options.add_argument('--verbose', '-v', action='count', default=0, help='Select Reframe\'s verbose level by specifying multiple v\'s')
    options.add_argument('--help', '-h', action='help', help='Display help and quit program')

    args = parser.parse_args()

    args.config = handleColonSeparator(args.config)
    args.dir = handleColonSeparator(args.dir)
    args.exclude = handleColonSeparator(args.exclude)

    argsValidation(args)

    return args


# not really useful as arguments can be passed multiple times with blank space or multiple -c
def handleColonSeparator(arg):
    splitted = []
    if isinstance(arg, list):
        for elem in arg:
            if ':' in elem:
                splitted.extend(elem.split(':'))
            else:
                splitted.append(elem)
        arg = splitted

    elif isinstance(arg, str):
        if ':' in arg:
            splitted.append(arg.split(':'))
    return arg


def printListAndExit(lst, name):
    for i,elem in enumerate(lst):
        print(f" > {name} {i+1}:", elem)
    sys.exit(1)


def argsValidation(args):
    if not args.config and not args.dir:
        print(f'[Error] At least one of --config or --dir option must be specified')
        sys.exit(1)

    if args.config and len(args.dir) > 1:
        print(f'[Error] --dir and --config combination can only handle one DIR')
        sys.exit(1)

    notFound = []
    if args.config:
        if not args.dir:
            for config in args.config:
                if not os.path.exists(config):
                    notFound.append(config)
        else:
            # args.dir is a list with 1 element
            dir = args.dir[0]
            for config in args.config:
                path = os.path.join(dir, config)
                if not os.path.exists(path):
                    notFound.append(config)

        if notFound:
            print(f'[Error] Following configuration files were not found')
            printListAndExit(notFound, 'file')

    elif args.dir:
        for dir in args.dir:
            if not os.path.isdir(dir):
                notFound.append(dir)
        if notFound:
            print(f'[Error] Following directories were not found')
            printListAndExit(notFound, 'dir')


def printArgs(args):
    print("\n[Loaded command-line options]")
    for arg in vars(args):
        print(f"\t > {arg + ':' :<{20}} {getattr(args, arg)}")
    print("\n" + '=' * shutil.get_terminal_size().columns)
