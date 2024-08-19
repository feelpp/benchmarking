import json
import sys
import os


supportedEnvVars = ('HOME', 'USER', 'WORKDIR', 'HOSTNAME', 'FEELPPDB_PATH', 'TOOLBOX')
validToolboxes = ('electric', 'fluid', 'heat', 'heatfluid', 'solid', 'thermoelectric')    # fsi, hdg: only unsteady cases in usr/share/...


class ConfigReader:

    def __init__(self, configPath):
        self.configPath = configPath
        self.data = None
        self.Reframe = None
        self.Feelpp = None
        self.Reporter = None
        self.load()
        self.processData()

    def load(self):
        # Error handling already done in launchProcess.py
        with open(self.configPath, 'r') as file:
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
            for var in supportedEnvVars:
                value = os.getenv(var, '')
                data = data.replace(f'${{{var}}}', value)
        return data


    def processData(self):
        self.Reframe = ReframeConfig(self.data['Reframe'])
        self.Feelpp = FeelppConfig(self.data['Feelpp'])
        self.Reporter = ReporterConfig(self.data['Reporter'])

    def __repr__(self):
        return json.dumps(self.data, indent=4)


#  Reframe Configuration
#  =====================

class ReframeConfig:
    def __init__(self, data):
        self.hostConfig = data['hostConfig']
        self.reportPrefix = data['reportPrefix']
        self.reportSuffix = data['reportSuffix']
        self.Directories = DirectoriesConfig(data['Directories'])
        self.Mode = ModeConfig(data['Mode'])


    def to_dict(self):
        return {
            "Host Configuration": self.hostConfig,
            "Report prefix": self.reportPrefix,
            "Report suffix": self.reportSuffix,
            "Directories": self.Directories.to_dict(),
            "Mode": self.Mode.to_dict()
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)


class DirectoriesConfig:
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


class ModeConfig:
    def __init__(self, data):
        self.name = data['type']
        self.exclusiveAccess = data['exclusiveAccess']
        self.topology = TopologyConfig(data['topology'])
        self.sequencing = SequencingConfig(data['sequencing'])

    def to_dict(self):
        return {
            "name": self.name,
            "topology": self.topology.to_dict(),
            "sequencing": self.sequencing.to_dict()
        }


class TopologyConfig:
    def __init__(self, data):
        self.minPhysicalCpuPerNode = data['minPhysicalCpuPerNode']
        self.maxPhysicalCpuPerNode = data['maxPhysicalCpuPerNode']
        self.minNodeNumber = data['minNodeNumber']
        self.maxNodeNumber = data['maxNodeNumber']

    def to_dict(self):
        return {
            "minPhysicalCpuPerNode": self.minPhysicalCpuPerNode,
            "maxPhysicalCpuPerNode": self.maxPhysicalCpuPerNode,
            "minNodeNumber": self.minNodeNumber,
            "maxNodeNumber": self.maxNodeNumber
        }


class SequencingConfig:
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

class FeelppConfig:
    """
    If partitioning set to false, you need to specify a single directory which contains every partitioning file.
    The files' naming scheme is the one provided by Feelpp Toolboxes, i.e. "filename_np{nbTask}"
    """
    def __init__(self, data):
        self.toolbox = data['toolbox']
        self.CommandLine = CommandLineConfig(data['CommandLine'])

        if self.toolbox not in validToolboxes:
            print("[Error] Unknown toolbox:\t", self.toolbox)
            sys.exit(1)


    def to_dict(self):
        return {
            "Toolbox": self.toolbox,
            "CommandLine": self.CommandLine.to_dict()
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)


class CommandLineConfig:
    def __init__(self, data):
        self.configFiles = data['config-files']
        self.repository = RepositoryConfig(data['repository'])
        self.case = CaseConfig(data['case'])
        self.json = JsonPatchConfig(data['jsonPatch'])
        #self.commandList = self.buildCommandList(data)


    def configFilesToStr(self):
        return ' '.join(elem for elem in self.configFiles)


    # Finally not used as we need Reframe's parametrization for paths building
    # (doesn't work yet for --json command line)
    def buildCommandList(self, data, prefix=''):
        commands = []
        for key, value in data.items():
            if (type(value) == str) and (value.strip() == ''):
                continue
            if key == 'config-files':
                commands.append(f'--{key} {self.configFilesToStr()}')
            elif isinstance(value, dict):
                commands.extend(self.buildCommandList(value, f'{prefix}{key}.'))
            else:
                commands.append(f'--{prefix}{key} {value}')
        return commands


    def to_dict(self):
        return {
            "Config-files": self.configFiles,
            "Repository": self.repository.to_dict(),
            "Case": self.case.to_dict(),
            "Json": self.json.to_dict()
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)


class RepositoryConfig:
    def __init__(self, data):
        self.prefix = data['prefix']
        self.case = data['case']

    def to_dict(self):
        return {
            "Prefix": self.prefix,
            "Case": self.case
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)


class CaseConfig:
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



class JsonPatchConfig:
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



# --heat-fluid.json.patch='{ "op": "replace", "path": "/Meshes/heatfluid/Import/filename", "value": "$cfgdir/meshpartitioning/'${MESH_INDEX}'/mesh_o_p$np.json" }'

#  Reporter Configuration       --> check if needed
#  ======================

class ReporterConfig:
    def __init__(self, data):
        self.active = data['active']
        self.scaling = data['scaling']

    def to_dict(self):
        return {
            "active": self.active,
            "scaling": self.scaling
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)



# For debugging purposes

if __name__ == '__main__':

    workdir = '/home/tanguy/Projet/benchmarking'
    relativePath = 'benchConfigs/heat/ThermalBridgesCase3.json'

    config = ConfigReader(configPath=os.path.join(workdir, relativePath))

    print('[LOADED CONFIGURATION]\n', config)
    print('\n[CONFIG_FILES]\n >', config.Feelpp.CommandLine.configFilesToStr())

    jsonCommands = config.Feelpp.CommandLine.json.commands
    print('\n[JSON_COMMANDS]\n >')
    print('\n >'.join(jsonCommands))

    caseCommands = config.Feelpp.CommandLine.case.commands
    if caseCommands:
        print('\n[JSON_COMMANDS]\n >')
        print(caseCommands)
        print('\n >'.join(caseCommands))