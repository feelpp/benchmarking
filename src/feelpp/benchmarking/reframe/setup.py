
from feelpp.benchmarking.reframe.parameters import ParameterHandler
from feelpp.benchmarking.reframe.config.configReader import ConfigReader, TemplateProcessor, FileHandler
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.resources import ResourceHandler


import reframe as rfm
import os, re, shutil, sys
import numpy as np
from copy import deepcopy


@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):
    """ Reframe test used to setup the regression test"""
    report_dir_path = variable(str, value=".")

    #set num_nodes as variable (as not implemented in reframe) - used for exporting
    num_nodes = variable(int)

    script = variable(str)
    error_log = variable(str)
    output_log = variable(str)
    custom_logs = variable(list, value=[])

    #TODO: Find a way to avoid env variables

    #====================== INIT READERS ==================#
    machine_reader = ConfigReader(
        str(os.environ.get("MACHINE_CONFIG_FILEPATH")),
        MachineConfig, "machine",
        "--dry-run" in sys.argv
    )

    app_reader = ConfigReader(
        str(os.environ.get("APP_CONFIG_FILEPATH")),
        ConfigFile, "app",
        "--dry-run" in sys.argv,
        [machine_reader]
    )
    #======================================================#

    use_case = variable(str,value=app_reader.config.use_case_name)
    platform = variable(str, value=machine_reader.config.platform)

    execution_policy = variable(str,value=machine_reader.config.execution_policy)

    parameter_handler = ParameterHandler(app_reader.config.parameters)
    for param_name,param_values in parameter_handler.parameters.items():
        locals()[param_name]=parameter(param_values)


    @run_after('init')
    def setEnvironmentVariables(self):
        for cfg in [self.machine_reader.config, self.app_reader.config]:
            for env_var_name,env_var_value in cfg.env_variables.items():
                os.environ[env_var_name] = env_var_value


    @run_after('init')
    def setValidEnvironments(self):
        self.valid_systems = [f"{self.machine_reader.config.machine}:{part}" for part in self.machine_reader.config.partitions]
        self.valid_prog_environs = self.machine_reader.config.prog_environments


    @run_after('init')
    def pruneParameterSpace(self):
        self.parameter_handler.pruneParameterSpace(self)


    @run_after('setup')
    def dispatchReaders(self):
        """Creates independent readers for each test"""
        self.machine_reader = deepcopy(self.machine_reader)
        self.app_reader = deepcopy(self.app_reader)

    @run_after('setup')
    def setInstanceHash(self):
        """Updates the setup with testcase related values"""
        self.app_reader.updateConfig({ "instance" : str(self.hashcode) })
        self.machine_reader.updateConfig({ "instance" : str(self.hashcode) })

    @run_after('setup')
    def setPlatform(self):
        platform = self.app_reader.config.platforms[self.machine_reader.config.platform]
        if self.machine_reader.config.platform != "builtin":
            self.container_platform.image = platform.image.name
            self.container_platform.options = platform.options + self.machine_reader.config.containers[self.machine_reader.config.platform].options
            self.container_platform.workdir = None

    @run_after('setup')
    def pruneEnvironments(self):
        if not self.machine_reader.config.environment_map:
            return
        current_partition_shortname = self.current_partition.fullname.split(":")[-1]
        if self.current_environ.name not in self.machine_reader.config.environment_map[current_partition_shortname]:
            self.valid_prog_environs = []
            self.valid_systems = []
            self.skip(f"Skiping: {self.current_environ.name } is not specified for partition {current_partition_shortname} : {self.machine_reader.config.environment_map[current_partition_shortname]}")


    @run_before('run')
    def setupParameters(self):
        for param_name,subparameters in self.parameter_handler.nested_parameter_keys.items():
            value = getattr(self,param_name)
            self.app_reader.updateConfig({ f"parameters.{param_name}.value":str(value) })
            self.machine_reader.updateConfig({ f"parameters.{param_name}.value":str(value) })
            for subparameter in subparameters:
                self.app_reader.updateConfig({ f"parameters.{param_name}.{subparameter}.value":str(value[subparameter]) })
                self.machine_reader.updateConfig({ f"parameters.{param_name}.{subparameter}.value":str(value[subparameter]) })

    @run_before('run')
    def copyInputFileDependencies(self):
        """ If input_user_dir exists, copies all files from input_user_dir to input_dataset_base_dir preservign the structure"""
        if not self.machine_reader.config.input_user_dir or not self.app_reader.config.input_file_dependencies:
            return

        print(f"==========================================================")
        print(f"     COPYING FILES FROM {self.machine_reader.config.input_user_dir} to {self.machine_reader.config.input_dataset_base_dir}   ")
        for input_file in self.app_reader.config.input_file_dependencies.values():
            print(f"\t {input_file}")
            source = os.path.join(self.machine_reader.config.input_user_dir, input_file)
            destination = os.path.join(self.machine_reader.config.input_dataset_base_dir, input_file)

            if os.path.exists(destination):
                print(f"{destination} exists, {input_file} will not be copied...")
                continue

            FileHandler.copyFile(os.path.dirname(destination),os.path.basename(destination),source)
        print("============================================================")


    @run_before('run')
    def setResources(self):
        ResourceHandler.setResources(self.app_reader.config.resources, self)
        self.num_cpus_per_task = 1

    @run_before('run')
    def cleanupDirectories(self):
        FileHandler.cleanupDirectory(self.app_reader.config.scalability.directory)

    @run_before('run')
    def setSchedOptions(self):
        """ Sets the necessary pre-run configurations"""
        self.job.launcher.options += self.current_partition.get_resource('launcher_options')
        self.job.options += ['--threads-per-core=1']

    @run_before('run')
    def setExecutable(self):
        if self.machine_reader.config.platform == "builtin":
            self.executable = self.app_reader.config.executable
            self.executable_opts = self.app_reader.config.options
        else:
            self.container_platform.command = f"{self.app_reader.config.executable} {' '.join(self.app_reader.config.options + self.app_reader.config.platforms[self.machine_reader.config.platform].append_app_options)}"


