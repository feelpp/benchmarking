import reframe as rfm
from feelpp.benchmarking.reframe.setup import ReframeSetup
from feelpp.benchmarking.reframe.validation import ValidationHandler
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler


import shutil, os

@rfm.simple_test
class RegressionTest(ReframeSetup):
    """ Class to execute reframe test.
    It should contain sanity functions and performance variable setting"""

    @run_before('run')
    def initHandlers(self):
        self.validation_handler = ValidationHandler(self.app_setup.reader.config.sanity)
        self.scalability_handler = ScalabilityHandler(self.app_setup.reader.config.scalability)

    @run_after('run')
    def executionGuard(self):
        if self.is_dry_run():
            self.skip("ReFrame is in dry-run mode, perormance and sanity are not going to be evaluated.")

    @run_after('run')
    def addRfmOutputFiles(self):
        with open(os.path.join(self.stagedir, self.job.script_filename), 'r') as f:
            self.script = f.read()

        with open(os.path.join(self.stagedir,self.job.stdout), 'r') as f:
            self.output_log = f.read()

        with open(os.path.join(self.stagedir,self.job.stderr), 'r') as f:
            self.error_log = f.read()

    @run_before('performance')
    def cleanupTempInputFiles(self):
        """ IF input_user_dir is defined, it will remove all copied files (present on input_file_dependencies).
        This will clean up empty directories (even if not created by rfm)
        """
        if self.machine_setup.reader.config.input_user_dir:
            for input_file in self.app_setup.reader.config.input_file_dependencies.values():
                os.remove(os.path.join(self.machine_setup.reader.config.input_dataset_base_dir,input_file))

            #Delete empty dirs
            for dirpath, dirnames, _ in os.walk(self.machine_setup.reader.config.input_dataset_base_dir, topdown=False):
                for dirname in dirnames:
                    directory = os.path.join(dirpath,dirname)
                    if not os.listdir(directory):
                        os.rmdir(directory)
                        print(f"Deleted empty directory: {directory}")

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
        self.app_setup.reset(self.machine_setup.reader.config)
        self.app_setup.updateConfig({ "instance" : str(self.hashcode) })
        self.app_setup.copyParametrizedDescriptionFile(self.report_dir_path,name=self.hashcode)

    @run_before("cleanup")
    def removeDirectories(self):
        if self.app_setup.reader.config.scalability.clean_directory:
            self.app_setup.cleanupDirectories()

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )