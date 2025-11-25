import reframe as rfm
from feelpp.benchmarking.reframe.setup import ReframeSetup, DEBUG
from feelpp.benchmarking.reframe.config.configReader import FileHandler
from feelpp.benchmarking.reframe.validation import ValidationHandler
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler

from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer


import shutil, os

@rfm.simple_test
class RegressionTest(ReframeSetup):
    """ Class to execute reframe test.
    It should contain sanity functions and performance variable setting"""

    @run_before('run')
    def initHandlers(self):
        self.validation_handler = ValidationHandler(self.app_reader.config.sanity)
        self.scalability_handler = ScalabilityHandler(self.app_reader.config.scalability)

    @run_after('run')
    def executionGuard(self):
        if self.is_dry_run():
            self.skip("ReFrame is in dry-run mode, perormance and sanity are not going to be evaluated.")

    @run_before('performance')
    def setPerfVars(self):
        self.perf_variables = {}
        self.perf_variables.update(
            self.scalability_handler.getPerformanceVariables(self.num_tasks)
        )
        self.perf_variables.update(
            self.scalability_handler.getCustomPerformanceVariables(self.perf_variables)
        )

    @run_before('performance')
    def copyParametrizedFiles(self):
        FileHandler.copyResource(
            self.app_reader.config.additional_files.parameterized_descriptions_filepath,
            os.path.join(self.report_dir_path,"partials"),
            self.hashcode
        )

    @run_before('performance')
    def renderLogs(self):
        logs_data = {}
        with open(os.path.join(self.stagedir, self.job.script_filename), 'r') as f:
            logs_data["script"] = f.read()

        with open(os.path.join(self.stagedir,self.job.stdout), 'r') as f:
            logs_data["output_log"] = f.read()

        with open(os.path.join(self.stagedir,self.job.stderr), 'r') as f:
            logs_data["error_log"] = f.read()
        logs_data["custom_logs"] = []
        for custom_log_file in self.app_reader.config.additional_files.custom_logs:
            if not os.path.exists(custom_log_file):
                DEBUG(f"{custom_log_file} does not exist, continuing...")
                continue
            with open(custom_log_file,"r") as f:
                logs_data["custom_logs"].append({
                    "filename":os.path.basename(custom_log_file),
                    "content":f.read()
                })

        renderer = TemplateRenderer(os.path.join(os.path.dirname(__file__),"templates"),"logs.adoc.j2")
        renderer.render(os.path.join(self.stagedir,"logs.adoc"),logs_data)

    @run_before('performance')
    def copyLogs(self):
        FileHandler.copyResource(
            os.path.join(self.stagedir,"logs.adoc"),
            os.path.join(self.report_dir_path,"logs"),
            self.hashcode
        )

    @run_before("cleanup")
    def removeDirectories(self):
        if self.app_reader.config.scalability.clean_directory:
            FileHandler.cleanupDirectory(self.app_reader.config.scalability.directory)
        if self.machine_reader.config.input_user_dir and self.app_reader.config.input_file_dependencies:
            DEBUG("REMOVING INPUT FILE DEPENDENCIES...")
            for input_dep in self.app_reader.config.input_file_dependencies.values():
                location = os.path.join(self.machine_reader.config.input_dataset_base_dir,input_dep)
                if os.path.isfile(location):
                    os.remove(location)
                elif os.path.isdir(location):
                    shutil.rmtree(location)
                DEBUG(f"\t DELETED {input_dep}")

            #Delete empty dirs
            for dirpath, dirnames, _ in os.walk(self.machine_reader.config.input_dataset_base_dir, topdown=False):
                for dirname in dirnames:
                    directory = os.path.join(dirpath,dirname)
                    if not os.listdir(directory):
                        os.rmdir(directory)
                        DEBUG(f"Deleted empty directory: {directory}")


    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )