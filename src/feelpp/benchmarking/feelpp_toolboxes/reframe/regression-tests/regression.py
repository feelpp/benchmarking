from feelpp.benchmarking.feelpp_toolboxes.reframe.parameters import NbTasks
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.reframe.validation import ValidationHandler
import os
import reframe as rfm

@rfm.simple_test
class RegressionTest(rfm.RunOnlyRegressionTest):

    config = ConfigReader(str(os.environ['JSON_CONFIG_PATH'])).config

    valid_systems = config.reframe.valid_systems
    valid_prog_environs = config.reframe.valid_prog_environs

    validation_handler = ValidationHandler(config.application.sanity)

    for param_name, param_data in config.reframe.parameters:
        if not param_data.active:
            continue

        match param_name:
            case "nb_tasks":
                nb_tasks = parameter(NbTasks(param_data).parametrize())
                break
            case "mesh_sizes":
                raise NotImplementedError
            case "meshes":
                raise NotImplementedError
            case "solvers":
                raise NotImplementedError
            case _:
                raise NotImplementedError

    @run_after('init')
    def setEnvVars(self):
        self.env_vars['OMP_NUM_THREADS'] = 1

    @run_after('init')
    def setTags(self):
        self.tags = {
            "is_partial",
            self.config.application.use_case_name,
            os.environ.get("EXEC_POLICY","serial")
        }

    @run_before('run')
    def setLaunchOptions(self):
        self.exclusive_access = self.config.reframe.exclusive_access
        self.job.launcher.options = ['-bind-to core']


    @run_before('run')
    def setExecutableOpts(self):
        self.executable = self.config.application.executable
        self.executable_opts = self.config.application.options


    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )