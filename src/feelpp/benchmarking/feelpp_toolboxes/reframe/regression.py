import reframe as rfm
from feelpp.benchmarking.feelpp_toolboxes.reframe.setup import ReframeSetup

@rfm.simple_test
class RegressionTest(ReframeSetup):

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )