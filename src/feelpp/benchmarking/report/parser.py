from argparse import ArgumentParser, RawTextHelpFormatter
from feelpp.benchmarking.reframe.parser import CustomHelpFormatter
import os, shutil


#TODO: Factorize with feelpp.reframe parser
class ReportArgParser():
    """ Class for parsing and validating command-line arguments for the report module"""
    def __init__(self):
        self.parser = ArgumentParser(formatter_class=CustomHelpFormatter, add_help=False,description="Render benchmarking reports")
        self.addArgs()
        self.args = self.parser.parse_args()

    def addArgs(self):
        """ Add arguments to the parser """
        self.parser.add_argument("--config-file", "-c", type=str, help="Path to the JSON config file", default="./reports/website_config.json")
        self.parser.add_argument("--remote-download-dir", "-do", type=str, help="Path to the output directory where remote reports will be downloaded", default="reports")
        self.parser.add_argument("--modules-path", "-m", type=str, help="Path to the modules directory where reports will be rendered", default="./docs/modules/ROOT/pages")
        self.parser.add_argument("--plot-configs", "-pc", type=str, nargs='+', action='extend', help="Path the a plot configuration to use for a given benchmark. To be used along with --patch-reports")
        self.parser.add_argument("--overview-config", "-oc", type=str, help="Path to the overview configuration file", default="./src/feelpp/benchmarking/report/config/overviewConfig.json")

    def checkDirectoriesExist(self):
        """ Check that directories passed as arguments exist in the filesystem"""
        for filepath in [self.args.config_file, self.args.overview_config,self.args.modules_path]:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found ({filepath})")

        for plot_config in self.args.plot_configs:
            if not os.path.exists(plot_config):
                raise FileNotFoundError(f"Modules path not found ({plot_config})")

    def normalizePaths(self):
        """Normalize paths passed as arguments"""
        self.args.config_file = os.path.normpath(self.args.remote_download_dir)
        self.args.remote_download_dir = os.path.normpath(self.args.remote_download_dir)
        self.args.modules_path = os.path.normpath(self.args.modules_path)
        self.args.overview_config = os.path.normpath(self.args.overview_config)
        self.args.plot_configs = [os.path.normpath(plot_config) for plot_config in self.args.plot_configs]


    def printArgs(self):
        """ Prints arguments on the standard output"""
        print("\n[Loaded command-line options]")
        for arg in vars(self.args):
            print(f"\t > {arg + ':' :<{20}} {getattr(self.args, arg)}")
        print("\n" + '=' * shutil.get_terminal_size().columns)