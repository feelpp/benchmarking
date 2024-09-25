import json
import sys
import os


supported_env_vars = ('HOME', 'USER', 'WORKDIR', 'HOSTNAME', 'FEELPPDB_PATH', 'TOOLBOX')
valid_toolboxes = ('electric', 'fluid', 'heat', 'heatfluid', 'solid', 'thermoelectric')    # fsi, hdg: only unsteady cases in usr/share/...


class ConfigReader:

    def __init__(self, config_path):
        self.config_path = config_path
        self.data = None
        self.reframe = None
        self.feelpp = None
        self.reporter = None
        self.load()
        self.processData()

    def load(self):
        # Error handling already done in launchProcess.py
        with open(self.config_path, 'r') as file:
            self.data = json.load(file)
            self.substituteEnvVars(self.data)


    def substituteEnvVars(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.substituteEnvVars(value)

        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self.substituteEnvVars(data[i])

        elif isinstance(data, str):
            for var in supported_env_vars:
                value = os.getenv(var, '')
                data = data.replace(f'${{{var}}}', value)
        return data


    def processData(self):
        self.reframe = ReframeConfig(self.data['Reframe'])
        self.feelpp = FeelppConfig(self.data['Feelpp'])
        self.reporter = ReporterConfig(self.data['Reporter'])

    def __repr__(self):
        return json.dumps(self.data, indent=4)


#  Reframe Configuration
#  =====================

class Config:
    def __init__(self, data):
        pass

    def to_dict(self):
        pass

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)

class ReframeConfig(Config):
    def __init__(self, data):
        self.host_config = data['hostConfig']
        self.report_prefix = data['reportPrefix']
        self.report_suffix = data['reportSuffix']
        self.directories = DirectoriesConfig(data['Directories'])
        self.mode = ModeConfig(data['Mode'])


    def to_dict(self):
        return {
            "Host Configuration": self.host_config,
            "Report prefix": self.report_prefix,
            "Report suffix": self.report_suffix,
            "Directories": self.directories.to_dict(),
            "Mode": self.mode.to_dict()
        }


class DirectoriesConfig(Config):
    def __init__(self, data):
        self.prefix = data['prefix']
        self.stage = data['stage']
        self.output = data['output']


    def to_dict(self):
        return {
            "prefix": self.prefix,
            "stage": self.stage,
            "output": self.output
        }


class ModeConfig(Config):
    def __init__(self, data):
        self.name = data['type']
        self.exclusive_access = data['exclusiveAccess']
        self.topology = TopologyConfig(data['topology'])
        self.sequencing = SequencingConfig(data['sequencing'])

    def to_dict(self):
        return {
            "name": self.name,
            "topology": self.topology.to_dict(),
            "sequencing": self.sequencing.to_dict()
        }


class TopologyConfig(Config):
    def __init__(self, data):
        self.min_physical_cpus_per_node = data['minPhysicalCpuPerNode']
        self.max_physical_cpus_per_node = data['maxPhysicalCpuPerNode']
        self.min_node_number = data['minNodeNumber']
        self.max_node_number = data['maxNodeNumber']

    def to_dict(self):
        return {
            "minPhysicalCpuPerNode": self.min_physical_cpus_per_node,
            "maxPhysicalCpuPerNode": self.max_physical_cpus_per_node,
            "minNodeNumber": self.min_node_number,
            "maxNodeNumber": self.max_node_number
        }


class SequencingConfig(Config):
    def __init__(self, data):
        # Generator: manual, power2, maxCPU, fixAllNodes        #TODO
        self.generator = data['generator']
        self.sequence = data['sequence']

    def to_dict(self):
        return {
            "generator": self.generator,
            "sequence": self.sequence
        }



#  Feelpp Configuration
#  =====================

class FeelppConfig(Config):
    """
    If partitioning set to false, you need to specify a single directory which contains every partitioning file.
    The files' naming scheme is the one provided by Feelpp Toolboxes, i.e. "filename_np{nbTask}"
    """
    def __init__(self, data):
        self.toolbox = data['toolbox']
        self.testCase = data["case_name"]
        self.CommandLine = CommandLineConfig(data['CommandLine'])

        if self.toolbox not in valid_toolboxes:
            print("[Error] Unknown toolbox:\t", self.toolbox)
            sys.exit(1)


    def to_dict(self):
        return {
            "Toolbox": self.toolbox,
            "CommandLine": self.CommandLine.to_dict()
        }


class CommandLineConfig(Config):
    def __init__(self, data):
        self.config_files = data['config-files']
        self.repository = RepositoryConfig(data['repository'])
        self.case = CaseConfig(data['case'])
        self.json = JsonPatchConfig(data['jsonPatch'])

    def configFilesToStr(self):
        return ' '.join(elem for elem in self.config_files)

    def to_dict(self):
        return {
            "Config-files": self.configFiles,
            "Repository": self.repository.to_dict(),
            "Case": self.case.to_dict(),
            "Json": self.json.to_dict()
        }


class RepositoryConfig(Config):
    def __init__(self, data):
        self.prefix = data['prefix']
        self.case = data['case']

    def to_dict(self):
        return {
            "Prefix": self.prefix,
            "Case": self.case
        }


class CaseConfig(Config):
    def __init__(self, data):
        self.dimension = data['dimension']
        self.discretization = data['discretization']
        self.commands = self.buildCaseCommands()

    def buildCaseCommands(self, prefix='--case'):
        commands = []
        if self.dimension != '':
            commands.append(f'{prefix}.dimension {self.dimension}')
        if self.discretization != '':
            commands.append(f'{prefix}.discretization {self.discretization}')
        return commands

    def to_dict(self):
        return {
            "dimension": self.dimension,
            "discretization": self.discretization
        }



class JsonPatchConfig(Config):
    def __init__(self, data):
        self.commands = []

        if isinstance(data, list):
            for jsonDict in data:
                if not self.containsEmpty(jsonDict):
                    cmd = self.buildPatchCommand(jsonDict)
                    self.commands.append(cmd)

        elif isinstance(data, dict):
            if not self.containsEmpty(data):
                cmd = self.buildPatchCommand(data)
                self.commands.append(cmd)


    def containsEmpty(self, data):
        return any(value == '' for value in data.values())


    def buildPatchCommand(self, data):
        # Construction de la commande avec le JSON correctement sérialisé
        cmd = "json.patch='" + json.dumps(data) + "'"
        return cmd


#  Reporter Configuration       --> check if needed
#  ======================

class ReporterConfig(Config):
    def __init__(self, data):
        self.active = data['active']
        self.scaling = data['scaling']

    def to_dict(self):
        return {
            "active": self.active,
            "scaling": self.scaling
        }