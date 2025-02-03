
from feelpp.benchmarking.reframe.parameters import ParameterFactory
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.outputs import OutputsHandler
from feelpp.benchmarking.reframe.resources import ResourceHandler


import reframe as rfm
import os, re, shutil, sys
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
        self.reader = ConfigReader(config_filepath,MachineConfig, dry_run = "--dry-run" in sys.argv)
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
        pass

    def dispatchEnvironments(self,rfm_test):
        if not self.reader.config.environment_map:
            return
        current_partition_shortname = rfm_test.current_partition.fullname.split(":")[-1]
        if rfm_test.current_environ.name not in self.reader.config.environment_map[current_partition_shortname]:
            rfm_test.valid_prog_environs = []
            rfm_test.valid_systems = []
            rfm_test.skip(f"Skiping: {rfm_test.current_environ.name } is not specified for partition {current_partition_shortname} : {self.reader.config.environment_map[current_partition_shortname]}")

    def setValidEnvironments(self, rfm_test):
        """ Sets the valid_systems and valid_prog_environs attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        #WARNING: If the partition does not exist, NO ERROR WILL BE THROWN. It will just be skipped.
        #Consider adding this to the docs
        rfm_test.valid_systems = [f"{self.reader.config.machine}:{part}" for part in self.reader.config.partitions]
        rfm_test.valid_prog_environs = self.reader.config.prog_environments

    def setPlatform(self, rfm_test,app_config):
        """ Sets the container_platform attributes
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        platform = app_config.platforms[self.reader.config.platform]
        if self.reader.config.platform != "builtin":
            rfm_test.container_platform.image = platform.image.name
            rfm_test.container_platform.options = platform.options + self.reader.config.containers[self.reader.config.platform].options
            rfm_test.container_platform.workdir = None

    def setTags(self,rfm_test):
        """ Sets the tags attribute
        Args:
            rfm_test (reframe class) : The test to apply the setup
        """
        rfm_test.tags = { self.reader.config.execution_policy }



class AppSetup(Setup):
    """ Application related setup"""
    def __init__(self,config_filepath,machine_config):
        """
        Args:
            config_filepath (str): Path of the application configuration json file
        """
        super().__init__()
        self.config_filepath = config_filepath
        self.reader = ConfigReader(config_filepath,ConfigFile, dry_run = "--dry-run" in sys.argv)

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
        self.setEnvVariables()

    def setEnvVariables(self):
        for env_var_name,env_var_value in self.reader.config.env_variables.items():
            os.environ[env_var_name] = env_var_value

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
    report_dir_path = variable(str, value=".")

    #set num_nodes as variable (as not implemented in reframe) - used for exporting
    num_nodes = variable(int)

    script = variable(str)
    error_log = variable(str)
    output_log = variable(str)

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
    def pruneParameterSpace(self):
        for param_config in self.app_setup.reader.config.parameters:
            if not param_config.conditions:
                continue

            active_parameter_value = str(getattr(self,param_config.name))
            filters_list = param_config.conditions.get(active_parameter_value)
            if not filters_list:
                continue

            active_filter_values = {}
            for filters in filters_list:
                for filter_name in filters.keys():
                    param_path = filter_name.split(".")
                    active_filter_values[filter_name] = getattr(self,param_path[0])
                    if len(param_path) > 1:
                        for p in param_path[1:]:
                            active_filter_values[filter_name] = active_filter_values[filter_name].get(p)

            is_valid = any(
                all(
                    active_filter_values[filter_key] in filter_values
                    for filter_key, filter_values in filters.items()
                )
                for filters in filters_list
            )

            self.skip_if(not is_valid , f"Invalid parameter combination ({active_filter_values}) for condition list {param_config.name}={active_parameter_value} condition list ({filters_list})", )

    @run_after('init')
    def setupAfterInit(self):
        """ Sets the necessary post-init configurations"""
        self.app_setup.setupAfterInit(self)
        self.machine_setup.setupAfterInit(self,self.app_setup.reader.config)

        #Used only to copy description
        temp_outputs_handler = OutputsHandler(self.app_setup.reader.config.additional_files)
        temp_outputs_handler.copyDescription(self.report_dir_path,name="description")

    @run_after('setup')
    def setupAfterSetup(self):
        self.machine_setup.dispatchEnvironments(self)

    @run_before('run')
    def updateSetups(self):
        """Updates the setup with testcase related values"""
        self.app_setup.reset(self.machine_setup.reader.config)
        self.app_setup.updateConfig({ "instance" : str(self.hashcode) })

    @run_before('run')
    def setupParameters(self):
        for param_name,subparameters in self.parameters.items():
            value = getattr(self,param_name)
            self.app_setup.updateConfig({ f"parameters.{param_name}.value":str(value) })
            for subparameter in subparameters:
                self.app_setup.updateConfig({ f"parameters.{param_name}.{subparameter}.value":str(value[subparameter]) })

    @run_before('run')
    def setResources(self):
        resources = self.app_setup.reader.config.resources
        ResourceHandler.setResources(resources, self)

        self.job.options += ['--threads-per-core=1']
        self.num_cpus_per_task = 1


    @run_before('run')
    def setupBeforeRun(self):
        """ Sets the necessary pre-run configurations"""
        self.job.launcher.options += self.current_partition.get_resource('launcher_options')

        self.machine_setup.setupBeforeRun(self)
        self.app_setup.setupBeforeRun(self,self.machine_setup.reader.config)