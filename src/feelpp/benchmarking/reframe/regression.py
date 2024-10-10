import reframe as rfm
from feelpp.benchmarking.reframe.setup import ReframeSetup

@rfm.simple_test
class RegressionTest(ReframeSetup):
    """ Class to execute reframe test.
    It should contain sanity functions and performance variable setting"""


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