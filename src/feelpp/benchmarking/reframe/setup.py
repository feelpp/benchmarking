
from feelpp.benchmarking.reframe.parameters import ParameterFactory
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.outputs import OutputsHandler

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
            for current_param_value, filters in param_config.conditions.items():
                if getattr(self,param_config.name) == current_param_value:
                    for accept_name,accept_values in filters.items():
                        param_path = accept_name.split(".")
                        current_filter_value = getattr(self,param_path[0])
                        if len(param_path) > 1:
                            for p in param_path[1:]:
                                current_filter_value = current_filter_value[p]
                        self.skip_if( current_filter_value not in accept_values,  f"{accept_name}={current_filter_value} not in {param_config.name}={current_param_value} condition list ({accept_values})", )

    @run_after('init')
    def setupAfterInit(self):
        """ Sets the necessary post-init configurations"""
        self.app_setup.setupAfterInit(self)
        self.machine_setup.setupAfterInit(self,self.app_setup.reader.config)

        #Used only to copy description
        temp_outputs_handler = OutputsHandler(self.app_setup.reader.config.outputs,self.app_setup.reader.config.additional_files)
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
    def setResources(self): #TODO: Maybe use strategy for this
        resources = self.app_setup.reader.config.resources
        if resources.tasks and resources.tasks_per_node:
            self.num_tasks_per_node = int(resources.tasks_per_node)
            self.num_tasks = int(resources.tasks)

            assert self.num_tasks % self.num_tasks_per_node == 0, f"Number of tasks is not divisible by tasks per node. ( {self.num_tasks} , {self.num_tasks_per_node})"
            assert self.num_tasks > 0 and self.num_tasks >= self.num_tasks_per_node > 0, "Tasks and tasks per node should be positive."
            assert self.num_tasks_per_node <= self.current_partition.processor.num_cpus, f"A node has not enough capacity ({self.current_partition.processor.num_cpus}, {self.num_tasks_per_node})"

        elif resources.tasks_per_node and resources.nodes:
            self.num_tasks_per_node = int(resources.tasks_per_node)
            self.num_nodes = int(resources.nodes)
            self.num_tasks = self.num_tasks_per_node * self.num_nodes

            assert self.num_tasks_per_node <= self.current_partition.processor.num_cpus, f"A node has not enough capacity ({self.current_partition.processor.num_cpus}, {self.num_tasks_per_node})"
            assert self.num_tasks > 0, "Number of tasks must be strictly positive"

        elif resources.tasks and resources.nodes:
            raise NotImplementedError("Number of tasks and Nodes combination is not yet supported")
            self.num_tasks = int(resources.tasks)
            self.num_nodes = int(resources.nodes)

            assert self.num_tasks > 0 and self.num_nodes > 0, "Number of Tasks and nodes should be strictly positive."
            assert self.num_nodes >= np.ceil(self.num_tasks/self.current_partition.processor.num_cpus), f"Cannot accomodate {self.num_tasks} tasks in {self.num_nodes} nodes"

        elif resources.tasks:
            self.num_tasks = int(resources.tasks)
            self.num_tasks_per_node = min(self.num_tasks,self.current_partition.processor.num_cpus)

            assert self.num_tasks > 0, "Number of Tasks and nodes should be strictly positive."

        else:
            raise ValueError("The Tasks parameter should contain either (tasks_per_node,nodes), (tasks,nodes), (tasks) or (tasks, tasks_per_node)")


        if resources.memory:
            nodes = int(np.ceil(int(resources.memory) / self.current_partition.extras["memory_per_node"]))
            if hasattr(self,"num_nodes"):
                self.num_nodes = nodes
            self.num_nodes = max(self.num_nodes,nodes)

            self.num_tasks_per_node = min(self.num_tasks_per_node, self.num_tasks // self.num_nodes)

        self.job.options += ['--threads-per-core=1']
        self.num_cpus_per_task = 1
        self.exclusive_access = bool(resources.exclusive_access) or True




    @run_before('run')
    def setupBeforeRun(self):
        """ Sets the necessary pre-run configurations"""
        self.job.launcher.options += self.current_partition.get_resource('launcher_options')

        self.machine_setup.setupBeforeRun(self)
        self.app_setup.setupBeforeRun(self,self.machine_setup.reader.config)