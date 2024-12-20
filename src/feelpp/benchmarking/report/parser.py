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
        self.validate()
        self.normalizePaths()

    def addArgs(self):
        """ Add arguments to the parser """
        self.parser.add_argument("--config-file", "-c", type=str, help="Path to the JSON config file", default="./reports/website_config.json")
        self.parser.add_argument("--remote-download-dir", "-do", type=str, help="Path to the output directory where remote reports will be downloaded", default="reports")
        self.parser.add_argument("--modules-path", "-m", type=str, help="Path to the modules directory where reports will be rendered", default="./docs/modules/ROOT/pages")
        self.parser.add_argument("--overview-config", "-oc", type=str, help="Path to the overview configuration file", default="./src/feelpp/benchmarking/report/config/overviewConfig.json"),
        self.parser.add_argument("--plot-configs", "-pc", type=str, nargs='+',default=[], action='extend', help="Path the a plot configuration to use for a given benchmark. To be used along with --patch-reports")
        self.parser.add_argument("--patch-reports","-pr", type=str, nargs='+',default=[], action='extend', help="Id of the reports to path, the syntax of the id is machine:application:usecase:date e.g. gaya:feelpp_app:my_use_case:2024_11_05T01_05_32. It is possible to affect all reports in a component by replacing the machine, application, use_case or date by 'all'. Also, one can indicate to patch the latest report by replacing the date by 'latest'. If this option is not provided but plot-configs is, then the latest report will be patched (most recent report date)")
        self.parser.add_argument("--save-patches","-sp", action='store_true', help="If this flag is active, existing plot configurations will be replaced with the ones provided in patch-reports.")
        self.parser.add_argument("--website","-w", action='store_true', help="Compile documentation and start HTTP server with benchmark reports")

    def validate(self):
        """ Validate specific options """
        self.checkDirectoriesExist()

        if self.args.patch_reports:
            for patch_report in self.args.patch_reports:
                splitted_patch = patch_report.split(":")
                if len(splitted_patch) != 4:
                    raise ValueError(f"The ID syntaxt is incorrect ({patch_report})")
                machine, app, use_case, date = splitted_patch
                if "latest" in [machine,app,use_case]:
                    raise ValueError("Latest not accepted for that component")
                if machine == "all":
                    raise ValueError("The machine component patch does not support the 'all' keyworkd")

            self.args.patch_reports = [patch_report.split(":") for patch_report in self.args.patch_reports]

    def checkDirectoriesExist(self):
        """ Check that directories passed as arguments exist in the filesystem"""
        for filepath in [self.args.config_file, self.args.overview_config,self.args.modules_path]:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found ({filepath})")

        for file in self.args.plot_configs:
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found ({file})")

    def normalizePaths(self):
        """Normalize paths passed as arguments"""
        self.args.config_file = os.path.normpath(self.args.config_file)
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