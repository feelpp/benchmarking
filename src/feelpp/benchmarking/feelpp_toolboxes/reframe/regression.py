from feelpp.benchmarking.feelpp_toolboxes.reframe.parameters import NbTasks
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.config.configSchema import ConfigFile,MachineConfig
from feelpp.benchmarking.feelpp_toolboxes.reframe.validation import ValidationHandler
import os
import reframe as rfm

@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):

    machine_config = ConfigReader(str(os.environ.get("EXEC_CONFIG_PATH")),MachineConfig).config
    app_config = ConfigReader(str(os.environ.get('JSON_CONFIG_PATH')),ConfigFile).config


    valid_systems = machine_config.valid_systems
    valid_prog_environs = machine_config.valid_prog_environs


    validation_handler = ValidationHandler(app_config.sanity)

    use_case = variable(str,value = app_config.use_case_name)

    for param_name, param_data in app_config.parameters:
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
        self.env_vars['OMP_NUM_THREADS'] = self.machine_config.omp_num_threads

    @run_after('init')
    def setTags(self):
        self.tags = {
            self.machine_config.execution_policy
        }

    @run_before('run')
    def setLaunchOptions(self):
        self.exclusive_access = self.machine_config.exclusive_access
        self.job.launcher.options = self.machine_config.launch_options

    @run_before('run')
    def setExecutableOpts(self):
        self.executable = self.app_config.executable
        self.executable_opts = self.app_config.options


@rfm.simple_test
class RegressionTest(ReframeSetup):

    @sanity_function
    def sanityCheck(self):
        return (
            self.validation_handler.check_success(self.stdout)
            and
            self.validation_handler.check_errors(self.stdout)
        )