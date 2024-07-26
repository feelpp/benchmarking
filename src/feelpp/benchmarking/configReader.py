import json
import sys
import os


supportedEnvVars = ('WORKDIR', 'HOME', 'USER', 'TB', 'HOSTNAME', 'FEELPPDB_PATH', 'RFM_TEST_DIR', 'MESH_INDEX', 'SOLVER_TYPE')


class ConfigReader:

    def __init__(self, mode, configPath='./benchConfig.json'):
        self.configPath = configPath
        self.data = None
        self.Reframe = None
        self.Feelpp = None
        self.Reporter = None
        self.load()
        self.processData(mode)

    def load(self):
        try:
            with open(self.configPath, 'r') as file:
                self.data = json.load(file)
                self.substituteEnvVars(self.data)

        except FileNotFoundError:
            print(f"Error: File {self.configPath} was not found.")
            sys.exit(1)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            sys.exit(1)


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

    def processData(self, mode):
        self.Reframe = ReframeConfig(self.data['Reframe'], mode)
        self.Feelpp = FeelppConfig(self.data['Feelpp'])
        self.Reporter = ReporterConfig(self.data['Reporter'])

    def __repr__(self):
        return json.dumps(self.data, indent=4)


#  Reframe Configuration
#  =====================

class ReframeConfig:
    def __init__(self, data, mode):
        self.globalConfig = data['globalConfig']
        self.hostConfig = data['hostConfig']
        self.Directories = DirectoriesConfig(data['Directories'])
        self.exclusiveAccess = data['exclusiveAccess']

        for modeDict in data['Modes']:
            if modeDict['type'] == mode:
                mode_data = modeDict
                break

        self.Mode = ModeConfig(mode_data)
        #self.exportEnvVars()


    """ !! Needed before launching Reframe !! """
    """
    # Reframe will automatically be launched with these configuration files (colon-separated),
    # instead of passing the -C command line option twice
    def exportEnvVars(self):
        os.environ['RFM_CONFIG_FILES'] = self.globalConfig + ':' + self.hostConfig
    """

    def to_dict(self):
        return {
            "General Configuration": self.globalConfig,
            "Host Configuration": self.hostConfig,
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
        self.testFiles = data['testFiles']
        self.reportPrefix = data['reportPrefix']
        #self.exportEnvVars()

    def exportEnvVars(self):
        os.environ['RFM_PREFIX'] = self.prefix
        os.environ['RFM_TEST_DIR'] = self.testFiles
        os.environ['RFM_REPORT_PREFIX'] = self.reportPrefix

    def to_dict(self):
        return {
            "prefix": self.prefix,
            "stage": self.stage,
            "output": self.output,
            "testFiles": self.testFiles,
            "report_path": self.report_path
        }


class ModeConfig:
    def __init__(self, data):
        self.name = data['type']
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
        #self.exportEnvVars()

    def exportEnvVars(self):
        os.environ['MIN_CPU'] = str(self.minPhysicalCpuPerNode)
        os.environ['MAX_CPU'] = str(self.maxPhysicalCpuPerNode)
        os.environ['MIN_NODES'] = str(self.minNodeNumber)
        os.environ['MAX_NODES'] = str(self.maxNodeNumber)

    def to_dict(self):
        return {
            "minPhysicalCpuPerNode": self.minPhysicalCpuPerNode,
            "maxPhysicalCpuPerNode": self.maxPhysicalCpuPerNode,
            "minNodeNumber": self.minNodeNumber,
            "maxNodeNumber": self.maxNodeNumber
        }


class SequencingConfig:
    def __init__(self, data):
        # Generator: manual, power2, maxCPU, fixAllNodes        TODO
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
        self.toolboxes = data['Toolboxes']
        self.casesDirectory = data['casesDirectory']
        self.partitioning = data['usePartitioning']
        self.CommandLine = CommandLineConfig(data['CommandLine'])
        if self.partitioning:
            if data['partitionDirectory'].strip() == '':
                print('[Error] Partitions directory is mandatory if partitioning=true')
                sys.exit(1)
            else:
                self.partDirectory = data['partitionDirectory'].strip()

        #self.exportEnvVars()

    """
    def exportEnvVars(self):
        os.environ['FEELPP_OUTPUT_PREFIX'] = self.outputPrefix
    """

    def to_dict(self):
        return {
            "Toolboxes": self.toolboxes,
            "Cases Directory": self.casesDirectory,
            "Partitioning": self.partitioning,
            "Partition Directory": self.partPath,
            "CommandLine": self.CommandLine.to_dict()
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)


class CommandLineConfig:
    def __init__(self, data):
        self.configFiles = data['config-files']
        self.repository = RepositoryConfig(data['repository'])
        self.case = CaseConfig(data['case'])
        self.commandList = self.buildCommandList(data)
        #self.exportEnvVars()

    def exportEnvVars(self):
        os.environ['FEELPP_CFG_PATHS'] = self.configFilesToStr()


    def configFilesToStr(self):
        return ' '.join(elem for elem in self.configFiles)

    # Finally not used
    def buildCommandList(self, data, prefix=''):
        commands = []
        for key, value in data.items():
            if (type(value) == str) and (value.strip() == ''):
                continue
            if key == 'config-files':
                cfgListToStr = ' '.join(str(cfg) for cfg in value)
                commands.append(f'--{key} {cfgListToStr}')
            elif isinstance(value, dict):
                commands.extend(self.buildCommandList(value, f'{prefix}{key}.'))
            else:
                commands.append(f'--{prefix}{key} {value}')
        return commands


    def to_dict(self):
        return {
            "Config-files": self.configFiles,
            "Repository": self.repository.to_dict(),
            "Case": self.case.to_dict()
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

    def to_dict(self):
        return {
            "dimension": self.dimension,
            "discretization": self.discretization
        }


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

    config = ConfigReader(mode="CpuVariation")
    print(config)
    print(' > test:', config.Feelpp.CommandLine.configFilesToStr())