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
        if self.app_setup.reader.config.additional_files and self.app_setup.reader.config.additional_files.parameterized_descriptions_filepath:
            self.app_setup.copyFile(
                self.app_setup.reader.config.additional_files.parameterized_descriptions_filepath,
                self.report_dir_path,
                self.hashcode
            )

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )