import shutil
from argparse import ArgumentParser, RawTextHelpFormatter



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

class BaseParser:
    def __init__(self,print_args=True,description=""):
        self.parser = ArgumentParser(formatter_class=CustomHelpFormatter, add_help=True,description=description)
        self.addArgs()
        self.args = self.parser.parse_args()
        if print_args:
            self.printArgs()
        self.processArgs()
        self.validate()

    def addArgs(self):
        raise NotImplementedError("This method should be implemented in child classes.")

    def validate(self):
        raise NotImplementedError("This method should be implemented in child classes.")

    def processArgs(self):
        pass

    def printArgs(self):
        """ Prints arguments on the standard output"""
        print("\n[Loaded command-line options]")
        for arg in vars(self.args):
            print(f"\t > {arg + ':' :<{20}} {getattr(self.args, arg)}")
        print("\n" + '=' * shutil.get_terminal_size().columns)

