
from feelpp.benchmarking.reframe.parameters import ParameterFactory
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.outputs import OutputsHandler

import reframe as rfm
import os, re, shutil
import numpy as np

##### TODO: This is very messy :( Rethink the design

class Setup:
    """ Abstract class for setup """
    def __init__(self):
        self.reader = None

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

    def updateConfig(self, replace = None):
        """ Replace the template values on the config attribute with variable values
        Args:
            replace (dict[str,str]): key,value pairs representing the placeholder name and the actual value to replace with
        """
        self.reader.updateConfig(replace)


class MachineSetup(Setup):
    """ Machine related setup"""
    def __init__(self,config_filepath):
        """
        Args:
            config_filepath (str): Path of the machine configuration json file
        """
        super().__init__()
        self.reader = ConfigReader(config_filepath,MachineConfig)
        self.updateConfig()

    def setupAfterInit(self,rfm_test,app_config):
        """ Methods to be executed after initialization step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        self.setValidEnvironments(rfm_test)
        self.setTags(rfm_test)
        self.setPlatform(rfm_test,app_config)

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
        rfm_test.valid_systems = [f"{self.reader.config.machine}:{part}" for part in self.reader.config.partitions]
        rfm_test.valid_prog_environs = self.reader.config.prog_environments

    def setPlatform(self, rfm_test,app_config):
        """ Sets the container_platform attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        platform = app_config.platforms[self.reader.config.platform]
        if self.reader.config.platform != "builtin":
            if not os.path.exists(platform.image.name):
                raise FileExistsError(f"Cannot find image {platform.image.name}")
            rfm_test.container_platform.image = platform.image.name
            rfm_test.container_platform.options = platform.options + self.reader.config.containers[self.reader.config.platform].options
            rfm_test.container_platform.workdir = None

    def setTags(self,rfm_test):
        """ Sets the tags attribute
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.tags = { self.reader.config.execution_policy }

    def setLaunchOptions(self, rfm_test):
        """ Sets the excusive_access and job.launcher.options attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.job.launcher.options = self.reader.config.launch_options



class AppSetup(Setup):
    """ Application related setup"""
    def __init__(self,config_filepath,machine_config):
        """
        Args:
            config_filepath (str): Path of the application configuration json file
        """
        super().__init__()
        self.config_filepath = config_filepath
        self.reader = ConfigReader(config_filepath,ConfigFile)

        self.updateConfig(self.reader.processor.flattenDict(machine_config,"machine"))
        self.updateConfig()


    def reset(self,machine_config):
        self.__init__(self.config_filepath,machine_config)

    def setupBeforeRun(self,rfm_test,machine_config):
        """ Methods to be executed before run step of a reframe test
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        self.cleanupDirectories()
        self.setExecutable(rfm_test,machine_config)

    def setupAfterInit(self, rfm_test):
        pass

    def cleanupDirectories(self):
        if os.path.exists(self.reader.config.scalability.directory):
            shutil.rmtree(self.reader.config.scalability.directory)


    def setExecutable(self, rfm_test, machine_config):
        """ Sets the executable and executable_opts attrbiutes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        if machine_config.platform == "builtin":
            rfm_test.executable = self.reader.config.executable
            rfm_test.executable_opts = self.reader.config.options
        else:
            rfm_test.container_platform.command = f"{self.reader.config.executable} {' '.join(self.reader.config.options)}"

@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):
    """ Reframe test used to setup the regression test"""
    report_dir_path = variable(str)

    #TODO: Find a way to avoid env variables
    machine_setup = MachineSetup(str(os.environ.get("MACHINE_CONFIG_FILEPATH")))
    app_setup = AppSetup(str(os.environ.get("APP_CONFIG_FILEPATH")),machine_setup.reader.config)

    use_case = variable(str,value=app_setup.reader.config.use_case_name)
    platform = variable(str, value=machine_setup.reader.config.platform)

    parameters = {}

    for param_config in app_setup.reader.config.parameters:
        if param_config.active:
            if param_config.mode=="zip":
                parameters[param_config.name] = [subparam.name for subparam in param_config.zip]
            elif param_config.mode=="sequence" and all(type(s)==dict and s.keys() for s in param_config.sequence):
                parameters[param_config.name] = list(param_config.sequence[0].keys())
            else:
                parameters[param_config.name] = []
            param_values = list(ParameterFactory.create(param_config).parametrize())
            exec(f"{param_config.name}=parameter({param_values})")

    @run_after('init')
    def setupAfterInit(self):
        """ Sets the necessary post-init configurations"""
        self.app_setup.setupAfterInit(self)
        self.machine_setup.setupAfterInit(self,self.app_setup.reader.config)

        #Used only to copy description
        temp_outputs_handler = OutputsHandler(self.app_setup.reader.config.outputs,self.app_setup.reader.config.additional_files)
        temp_outputs_handler.copyDescription(self.report_dir_path,name="description")


    @run_before('run')
    def updateSetups(self):
        """Updates the setup with testcase related values"""
        self.app_setup.reset(self.machine_setup.reader.config)
        self.app_setup.updateConfig({ "instance" : str(self.hashcode) })

    @run_before('run')
    def setupParameters(self):
        for param_name,subparameters in self.parameters.items():
            value = getattr(self,param_name)
            if param_name == "nb_tasks":
                self.num_tasks_per_node = min(int(value["tasks"]) // int(value["nodes"]), self.current_partition.processor.num_cpus)
                self.num_cpus_per_task = 1
                self.num_tasks = value["tasks"]

                self.exclusive_access = value["exclusive_access"] if "exclusive_access" in value else True

            self.app_setup.updateConfig({ f"parameters.{param_name}.value":str(value) })
            for subparameter in subparameters:
                self.app_setup.updateConfig({ f"parameters.{param_name}.{subparameter}.value":str(value[subparameter]) })




    @run_before('run')
    def setupBeforeRun(self):
        """ Sets the necessary pre-run configurations"""
        self.machine_setup.setupBeforeRun(self)
        self.app_setup.setupBeforeRun(self,self.machine_setup.reader.config)
