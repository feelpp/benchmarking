import json
import sys


class ConfigReader:

    def __init__(self, configPath='./benchConfig.json'):
        self.configPath = configPath
        self.data = None
        self.Reframe = None
        self.Feelpp = None
        self.load()
        self.processData()

    def load(self):
        try:
            with open(self.configPath, 'r') as file:
                self.data = json.load(file)

        except FileNotFoundError:
            print(f"Error: File {self.configPath} was not found.")
            sys.exit(1)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            sys.exit(1)


    def processData(self):
        self.Reframe = ReframeConfig(self.data['Reframe'])
        self.Feelpp = FeelppConfig(self.data['Feelpp'])

    def varExporter(self):
        print(f'export RFM_DIR={self.Reframe.Directories.testFiles}')
        print(f'export RFM_CONFIG_PATH={self.Reframe.Directories.RFM_CONFIG_PATH}')

    def __repr__(self):
        return json.dumps(self.data, indent=4)



#  Reframe Configuration
#  =====================

class ReframeConfig:
    def __init__(self, data):
        self.Directories = DirectoriesConfig(data['Directories'])
        self.Mode = ModeConfig(data['Mode'])

    def __repr__(self):
        return json.dumps( {"Directories": self.Directories.__dict__,
                            "Mode": self.Mode.__dict__ },
                            indent=4)


class DirectoriesConfig:
    def __init__(self, data):
        self.stage = data['stage']
        self.output = data['output']
        self.testFiles = data['testFiles']
        self.RFM_CONFIG_PATH = data['clusterConfig']


class ModeConfig:
    def __init__(self, data):
        self.singleNode = data['singleNode']
        self.minPhysicalCpuPerNode = data['minPhysicalCpuPerNode']
        self.maxPhysicalCpuPerNode = data['maxPhysicalCpuPerNode']
        self.minNodeNumber = data['minNodeNumber']
        self.maxNodeNumber = data['maxNodeNumber']


#  Feelpp Configuration
#  =====================

class FeelppConfig:
    def __init__(self, data):
        self.Paths = PathsConfig(data['Paths'])
        self.CommandLine = CommandLineConfig(data['CommandLine'])

    def __repr__(self):
        return json.dumps( {"Paths": self.Paths.__dict__,
                            "CommandLine": self.CommandLine.__dict__},
                            indent=4)


class PathsConfig:
    def __init__(self, data):
        self.casesDirectory = data['casesDirectory']


class CommandLineConfig:
    def __init__(self, data):
        self.config_files = data['config-files']
        self.repository = RepositoryConfig(data['repository'])
        self.case = CaseConfig(data['case'])
        #self.gmsh = GmshConfig(data['gmsh'])
        self.commands = self.buildCommandList(data)

    def buildCommandList(self, data, prefix=''):
        commands = []
        for key, value in data.items():
            if isinstance(value, dict):
                commands.extend(self.buildCommandList(value, f'{prefix}{key}.'))
            else:
                commands.append(f'--{prefix}{key} {value}')
        return commands

    def __repr__(self):
        return self.commands



class RepositoryConfig:
    def __init__(self, data):
        self.prefix = data['prefix']
        self.case = data['case']


class CaseConfig:
    def __init__(self, data):
        self.dimension = data['dimension']
        self.discretization = data['discretization']

"""
class GmshConfig:
    def __init__(self, data):
        self.hsize = data['hsize']
"""



if __name__ == '__main__':

    config = ConfigReader()

    if len(sys.argv) > 1 and sys.argv[1] == '--from-launcher':
        config.varExporter()

    else:
        try:
            print('[MAIN] - not from launcher')
            """
            print('START_print')
            print(config)
            print('END_print')
            print('[test1] config.Reframe.Directories.testFiles =', config.Reframe.Directories.testFiles)
            print('[test2] config.Feelpp.CommandLine.repository.prefix =', config.Feelpp.CommandLine.repository.prefix)
            """
            print(config.Feelpp.CommandLine.commands)


        except KeyError as e:
            print(f"Configuration error: {e}")