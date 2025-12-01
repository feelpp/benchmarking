
from feelpp.benchmarking.reframe.parameters import ParameterHandler
from feelpp.benchmarking.reframe.config.configReader import ConfigReader, TemplateProcessor, FileHandler
from feelpp.benchmarking.reframe.schemas.benchmarkSchemas import ConfigFile
from feelpp.benchmarking.reframe.schemas.machines import MachineConfig
from feelpp.benchmarking.reframe.resources import ResourceHandler


import reframe as rfm
import os, re, shutil, sys
import numpy as np
from copy import deepcopy


DEBUG = lambda msg: print(msg) if os.environ.get("FEELPP_BENCHMARKING_DEBUG",0)==1 else None

@rfm.simple_test
class ReframeSetup(rfm.RunOnlyRegressionTest):
    """ Reframe test used to setup the regression test"""
    report_dir_path = variable(str, value=".")

    #set num_nodes as variable (as not implemented in reframe) - used for exporting
    num_nodes = variable(int)

    #TODO: Find a way to avoid env variables

    #====================== INIT READERS ==================#
    configs = [{"":str(os.environ.get("APP_CONFIG_FILEPATH"))}]
    machine_path = os.environ.get("MACHINE_CONFIG_FILEPATH")
    if machine_path:
        configs += [{"machine":str(machine_path)}]

    app_reader = ConfigReader(configs,ConfigFile,"app",dry_run="--dry-run" in sys.argv)

    #======================================================#

    use_case = variable(str,value=app_reader.config.use_case_name)
    platform = variable(str, value=app_reader.config.machine.platform)
    check_params = variable(dict)

    execution_policy = variable(str,value=app_reader.config.machine.execution_policy)

    parameter_handler = ParameterHandler(app_reader.config.parameters)
    for param_name,param_values in parameter_handler.parameters.items():
        locals()[param_name]=parameter(param_values)


    @run_after('init')
    def setEnvironmentVariables(self):
        for cfg in [self.app_reader.config.machine, self.app_reader.config]:
            for env_var_name,env_var_value in cfg.env_variables.items():
                os.environ[env_var_name] = env_var_value


    @run_after('init')
    def setValidEnvironments(self):
        self.valid_systems = [f"{self.app_reader.config.machine.machine}:{part}" for part in self.app_reader.config.machine.partitions]
        self.valid_prog_environs = self.app_reader.config.machine.prog_environments


    @run_after('init')
    def pruneParameterSpace(self):
        self.parameter_handler.pruneParameterSpace(self)



    @run_after('setup')
    def dispatchReaders(self):
        """Creates independent readers for each test"""
        self.app_reader = deepcopy(self.app_reader)

    @run_after('setup')
    def setInstanceHash(self):
        """Updates the setup with testcase related values"""
        self.app_reader.updateConfig({ "instance" : str(self.hashcode) })

    @run_after('setup')
    def setPlatform(self):
        platform = self.app_reader.config.platforms[self.app_reader.config.machine.platform]
        if self.app_reader.config.machine.platform != "builtin":
            self.container_platform.image = platform.image.filepath
            self.container_platform.options = platform.options + self.app_reader.config.machine.containers[self.app_reader.config.machine.platform].options
            self.container_platform.workdir = None

    @run_after('setup')
    def pruneEnvironments(self):
        if not self.app_reader.config.machine.environment_map:
            return
        current_partition_shortname = self.current_partition.fullname.split(":")[-1]
        if self.current_environ.name not in self.app_reader.config.machine.environment_map[current_partition_shortname]:
            self.valid_prog_environs = []
            self.valid_systems = []
            self.skip(f"Skiping: {self.current_environ.name } is not specified for partition {current_partition_shortname} : {self.app_reader.config.machine.environment_map[current_partition_shortname]}")


    @run_before('run')
    def setupParameters(self):
        for param_name,subparameters in self.parameter_handler.nested_parameter_keys.items():
            value = getattr(self,param_name)
            self.app_reader.updateConfig({ f"parameters.{param_name}.value":str(value) })
            for subparameter in subparameters:
                self.app_reader.updateConfig({ f"parameters.{param_name}.{subparameter}.value":str(value[subparameter]) })

    @run_before('run')
    def setCheckParams(self):
        params = {}
        for param_name,subparameters in self.parameter_handler.nested_parameter_keys.items():
            params[param_name] = getattr(self,param_name)
        self.check_params = params

    @run_before('run')
    def copyInputFileDependencies(self):
        """ If input_user_dir exists, copies all files from input_user_dir to input_dataset_base_dir preservign the structure"""
        if not self.app_reader.config.machine.input_user_dir or not self.app_reader.config.input_file_dependencies:
            return

        DEBUG(f"==========================================================")
        DEBUG(f"     COPYING FILES FROM {self.app_reader.config.machine.input_user_dir} to {self.app_reader.config.machine.input_dataset_base_dir}   ")
        for input_dep_name,input_dep in self.app_reader.config.input_file_dependencies.items():
            DEBUG(f"\t {input_dep}")
            source = os.path.join(self.app_reader.config.machine.input_user_dir, input_dep)
            if not os.path.exists(source):
                raise FileNotFoundError(f"Did not found input dependency {input_dep_name}")

            destination = os.path.join(self.app_reader.config.machine.input_dataset_base_dir, input_dep)

            if os.path.exists(destination):
                DEBUG(f"{destination} exists, {input_dep} will not be copied...")
                continue
            FileHandler.copyResource(source,os.path.dirname(destination) if os.path.isfile(source) else destination)
        DEBUG("============================================================")

    @run_before('run')
    def checkInputFileDependencies(self):
        if not self.app_reader.config.input_file_dependencies:
            return

        for input_dep_name, input_dep in self.app_reader.config.input_file_dependencies.items():
            if os.path.isabs(input_dep):
                if not os.path.exists(input_dep):
                    raise FileNotFoundError(f"Input dependency {input_dep_name} not found in {input_dep}")
            else:
                expected_path = os.path.join(self.app_reader.config.machine.input_dataset_base_dir,input_dep)
                if not os.path.exists(expected_path):
                    raise FileNotFoundError(f"Input dependency {input_dep_name} not found in {expected_path}")


    @run_before('run')
    def setResources(self):
        ResourceHandler.setResources(self.app_reader.config.resources, self)
        self.num_cpus_per_task = 1

    @run_before('run')
    def cleanupDirectories(self):
        if self.app_reader.config.scalability:
            FileHandler.cleanupDirectory(self.app_reader.config.scalability.directory)

    @run_before('run')
    def setSchedOptions(self):
        """ Sets the necessary pre-run configurations"""
        self.job.launcher.options += self.current_partition.get_resource('launcher_options')
        self.job.options += self.app_reader.config.machine.access
        self.job.options += ['--threads-per-core=1']

    @run_before('run')
    def setExecutable(self):
        if self.app_reader.config.machine.platform == "builtin":
            self.executable = self.app_reader.config.executable
            self.executable_opts = self.app_reader.config.options
        else:
            self.container_platform.command = f"{self.app_reader.config.executable} {' '.join(self.app_reader.config.options + self.app_reader.config.platforms[self.app_reader.config.machine.platform].append_app_options)}"


