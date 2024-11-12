import reframe as rfm
from feelpp.benchmarking.reframe.setup import ReframeSetup
from feelpp.benchmarking.reframe.validation import ValidationHandler
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler
from feelpp.benchmarking.reframe.outputs import OutputsHandler


import shutil

@rfm.simple_test
class RegressionTest(ReframeSetup):
    """ Class to execute reframe test.
    It should contain sanity functions and performance variable setting"""

    @run_before('run')
    def initHandlers(self):
        self.validation_handler = ValidationHandler(self.app_setup.config.sanity)
        self.scalability_handler = ScalabilityHandler(self.app_setup.config.scalability)
        self.outputs_handler = OutputsHandler(self.app_setup.config.outputs, self.app_setup.config.additional_files)

    @run_before('performance')
    def setPerfVars(self):
        self.perf_variables = {}
        self.perf_variables.update(
            self.scalability_handler.getPerformanceVariables(self.nb_tasks["tasks"])
        )
        self.perf_variables.update(
            self.outputs_handler.getOutputs()
        )


    @run_before('performance')
    def copyParametrizedFiles(self):
        self.outputs_handler.copyParametrizedDescriptions(self.report_dir_path,self.hashcode)

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )