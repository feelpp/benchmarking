import reframe as rfm
from feelpp.benchmarking.reframe.setup import ReframeSetup
from feelpp.benchmarking.reframe.validation import ValidationHandler
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler

import shutil

@rfm.simple_test
class RegressionTest(ReframeSetup):
    """ Class to execute reframe test.
    It should contain sanity functions and performance variable setting"""

    @run_before('run')
    def initHandlers(self):
        self.validation_handler = ValidationHandler(self.app_setup.config.sanity)
        self.scalability_handler = ScalabilityHandler(self.app_setup.config.scalability)

    @run_before('performance')
    def setPerfVars(self):
        self.perf_variables = self.scalability_handler.getPerformanceVariables(self.nb_tasks)

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )

    @run_after('cleanup')
    def cleanupApplicationFiles(self):
        #TODO: CAN BE DANGEROUS ?
        shutil.rmtree(self.app_setup.config.scalability.directory)