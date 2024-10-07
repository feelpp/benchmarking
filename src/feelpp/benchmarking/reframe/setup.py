
from feelpp.benchmarking.reframe.parameters import NbTasks,Discretization
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile,MachineConfig

import reframe as rfm
import os, re

class Setup:
    """ Abstract class for setup """
    def __init__(self):
        self.config = None

    def setupAfterInit(self, rfm_test):
        """ Pure virtual function
        Methods to be executed after initialization step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        pass

    def setupBeforeRun(self, rfm_test):
        """ Pure virtual function
        Methods to be executed before run step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        pass

class MachineSetup(Setup):
    """ Machine related setup"""
    def __init__(self,config_filepath):
        """
        Args:
            config_filepath (str): Path of the machine configuration json file
        """
        super().__init__()
        self.config = ConfigReader(config_filepath,MachineConfig).config

    def setupAfterInit(self,rfm_test):
        """ Methods to be executed after initialization step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        self.setValidEnvironments(rfm_test)
        self.setEnvVars(rfm_test)
        self.setTags(rfm_test)

    def setupBeforeRun(self,rfm_test):
        """ Methods to be executed before run step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        self.setLaunchOptions(rfm_test)

    def setValidEnvironments(self, rfm_test):
        """ Sets the valid_systems and valid_prog_environs attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.valid_systems = self.config.valid_systems
        rfm_test.valid_prog_environs = self.config.valid_prog_environs

    def setEnvVars(self,rfm_test):
        """ Sets the env_vars attribute
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.env_vars['OMP_NUM_THREADS'] = self.config.omp_num_threads

    def setTags(self,rfm_test):
        """ Sets the tags attribute
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.tags = { self.config.execution_policy }

    def setLaunchOptions(self, rfm_test):
        """ Sets the excusive_access and job.launcher.options attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.exclusive_access = self.config.exclusive_access
        rfm_test.job.launcher.options = self.config.launch_options


class AppSetup(Setup):
    """ Application related setup"""
    def __init__(self,config_filepath):
        """
        Args:
            config_filepath (str): Path of the application configuration json file
        """
        super().__init__()
        self.config_filepath = config_filepath
        self.config = ConfigReader(config_filepath,ConfigFile).config

        self.template_pattern = re.compile(r"\{\{(.*?)\}\}")

    def reset(self):
        self.__init__(self.config_filepath)

    def setupBeforeRun(self,rfm_test):
        """ Methods to be executed before run step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        self.setExecutable(rfm_test)

    def setExecutable(self, rfm_test):
        """ Sets the executable and executable_opts attrbiutes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.executable = self.config.executable
        rfm_test.executable_opts = self.config.options

    def replaceField(self,field, replace):
        """ Replaces a single string {{stored.like.this}} with their actual replace value
        Args:
            field (str): The string to find the template
            replace (str): The value to replace with
        """
        return self.template_pattern.sub(lambda match: replace.get(match.group(1).strip(), match.group(0)), field)

    def updateDict(self, obj, replace):
        """ Replaces template values {{stored.like.this}} with their actual values
        Args:
            obj (dict): The dictionary containing the templates
            replace (dict): key,value pairs representing the placeholder name and the actual value to replace with
        """
        new_cfg = {}

        for field, value in obj.items():
            if isinstance(value, dict):
                new_cfg[field] = self.updateDict(value, replace)
            elif isinstance(value, list):
                new_cfg[field] = [self.replaceField(v,replace) if isinstance(v, str) else v for v in value ]
            elif isinstance(value, str):
                new_cfg[field] = self.replaceField(value,replace)
            else:
                new_cfg[field] = value

        return new_cfg

    def updateConfig(self, replace):
        """ Replace the template values on the config attribute with variable values
        Args:
            replace (dict[str,str]): key,value pairs representing the placeholder name and the actual value to replace with
        """
        self.config = ConfigFile(** self.updateDict(self.config.model_dump(),replace))

@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):
    """ Reframe test used to setup the regression test"""
    machine_config_path = variable(str)

    #TODO: Find a way to avoid env variables
    app_setup = AppSetup(str(os.environ.get("APP_CONFIG_FILEPATH")))

    use_case = variable(str,value=app_setup.config.use_case_name)

    for param_name, param_data in app_setup.config.parameters:
        if not param_data.active:
            continue
        match param_name:
            case "nb_tasks":
                nb_tasks = parameter(NbTasks(param_data).parametrize())
            case "discretization":
                if param_data.type=="continuous":
                    hsize = parameter(Discretization(param_data).parametrize())
            case _:
                raise NotImplementedError


    @run_after('init')
    def initSetups(self):
        """ Initialize setups"""
        self.machine_setup = MachineSetup(self.machine_config_path)

    @run_after('init')
    def setupAfterInit(self):
        """ Sets the necessary post-init configurations"""
        self.machine_setup.setupAfterInit(self)
        self.app_setup.setupAfterInit(self)

    @run_before('run')
    def updateSetups(self):
        """Updates the setup with testcase related values"""
        self.app_setup.reset()

    @run_before('run')
    def setupParameters(self):
        """ Assings parameters to actual reframe attributes, depending on the test"""
        if hasattr(self,"nb_tasks"):
            self.num_tasks_per_node = min(self.nb_tasks, self.current_partition.processor.num_cpus)
            self.num_cpus_per_task = 1
            self.num_tasks = self.nb_tasks
        if hasattr(self, "hsize"):
            self.app_setup.updateConfig({ "parameters.discretization.value":str(self.hsize) })

        self.app_setup.updateConfig({ "instance": str(self.hashcode) })


    @run_before('run')
    def setupBeforeRun(self):
        """ Sets the necessary pre-run configurations"""
        self.machine_setup.setupBeforeRun(self)
        self.app_setup.setupBeforeRun(self)
