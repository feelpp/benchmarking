
from feelpp.benchmarking.feelpp_toolboxes.reframe.parameters import NbTasks
from feelpp.benchmarking.feelpp_toolboxes.config.configReader import ConfigReader
from feelpp.benchmarking.feelpp_toolboxes.config.configSchemas import ConfigFile,MachineConfig
from feelpp.benchmarking.feelpp_toolboxes.reframe.validation import ValidationHandler
from feelpp.benchmarking.feelpp_toolboxes.reframe.scalability import ScalabilityHandler

import reframe as rfm
import os

class Setup:
    def __init__(self):
        self.config = None

    def setupAfterInit(self, rfm_test):
        pass

    def setupBeforeRun(self, rfm_test):
        pass

class MachineSetup(Setup):
    def __init__(self,config_filepath):
        super().__init__()
        self.config = ConfigReader(config_filepath,MachineConfig).config

    def setupAfterInit(self,rfm_test):
        self.setValidEnvironments(rfm_test)
        self.setEnvVars(rfm_test)
        self.setTags(rfm_test)

    def setupBeforeRun(self,rfm_test):
        self.setLaunchOptions(rfm_test)

    def setValidEnvironments(self, rfm_test):
        rfm_test.valid_systems = self.config.valid_systems
        rfm_test.valid_prog_environs = self.config.valid_prog_environs

    def setEnvVars(self,rfm_test):
        rfm_test.env_vars['OMP_NUM_THREADS'] = self.config.omp_num_threads

    def setTags(self,rfm_test):
        rfm_test.tags = { self.config.execution_policy }

    def setLaunchOptions(self, rfm_test):
        rfm_test.exclusive_access = self.config.exclusive_access
        rfm_test.job.launcher.options = self.config.launch_options


class AppSetup(Setup):
    def __init__(self,config_filepath):
        super().__init__()
        self.config = ConfigReader(config_filepath,ConfigFile).config

    def setupBeforeRun(self,rfm_test):
        self.setExecutable(rfm_test)

    def setExecutable(self, rfm_test):
        rfm_test.executable = self.config.executable
        rfm_test.executable_opts = self.config.options

@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):
    machine_config_path = variable(str)

    app_setup = AppSetup(str(os.environ.get("APP_CONFIG_FILEPATH")))

    use_case = variable(str,value=app_setup.config.use_case_name)

    for param_name, param_data in app_setup.config.parameters:
        if not param_data.active:
            continue
        match param_name:
            case "nb_tasks":
                nb_tasks = parameter(NbTasks(param_data).parametrize())
            case _:
                raise NotImplementedError

    validation_handler = ValidationHandler(app_setup.config.sanity)
    scalability_handler = ScalabilityHandler(app_setup.config.scalability)

    @run_after('init')
    def initSetups(self):
        self.machine_setup = MachineSetup(self.machine_config_path)

    @run_after('init')
    def setupAfterInit(self):
        self.machine_setup.setupAfterInit(self)
        self.app_setup.setupAfterInit(self)
        self.scalability_handler.cleanupScalabilityFiles()

    @run_before('run')
    def setupBeforeRun(self):
        self.machine_setup.setupBeforeRun(self)
        self.app_setup.setupBeforeRun(self)

    @run_before('run')
    def setupParameters(self):
        if hasattr(self,"nb_tasks"):
            self.num_tasks_per_node = min(self.nb_tasks, self.current_partition.processor.num_cpus)
            self.num_cpus_per_task = 1
            self.num_tasks = self.nb_tasks
        if hasattr(self, "mesh_size"):
            raise NotImplementedError
        if hasattr(self, "meshes"):
            raise NotImplementedError
        if hasattr(self, "solvers"):
            raise NotImplementedError

