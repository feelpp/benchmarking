import shutil
import glob
from setup import *


@rfm.simple_test
class ToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'

    toolbox = variable(str, value='')
    case = variable(str, value='')
    valuesPath = variable(str, value='')


    """ check what is needed """
    #checkers = variable(str, value='')             --> NEEDED
    #visualization = variable(str, value='')        --> DON'T THINK SO (complicated: use of export-scene-macro.py)
    #partitioning = variable(str, value='')         --> MAYBE


    @run_after('init')
    def setVariables(self):
        self.toolbox = self.config.Feelpp.toolbox
        self.case = self.config.Feelpp.CommandLine.configFilesToStr()


    @run_after('init')
    def buildPaths(self):
        # Extends output path with 'np_{task_number}'
        self.feelOutputSuffix = os.path.join(self.config.Feelpp.CommandLine.repository.case, f'np_{self.nbTask}')
        self.feelOutputPath = os.path.join(self.config.Feelpp.CommandLine.repository.prefix, f'{self.feelOutputSuffix}')
        #self.valuesPath = os.path.join(self.feelOutputPath, f'{self.toolbox}.measures/values.csv')


    @run_before('run')
    def cleanFolder(self):
        if os.path.exists(self.feelOutputPath):
            print(" >>> Cleaning Feelpp output folder...")
            shutil.rmtree(self.feelOutputPath)
        else:
            print(" >>> New folder will be created...")


    @run_before('run')
    def set_executable_opts(self):

        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-files {self.case}',
                                f'--repository.prefix {self.config.Feelpp.CommandLine.repository.prefix}',
                                f'--repository.case {self.feelOutputSuffix}',
                                '--fail-on-unknown-option 1']

        # json commands needs the '--toolbox' prefix,
        if self.config.Feelpp.CommandLine.json.commands:
            # scale files for heatfluid are named 'heat-fluid'
            toolbox = 'heat-fluid' if self.toolbox == 'heatfluid' else self.toolbox
            for cmd in self.config.Feelpp.CommandLine.json.commands:
                cmd = f'--{toolbox}.' + cmd
                self.executable_opts.append(cmd)

        if self.config.Feelpp.CommandLine.case.commands:
            self.executable_opts.extend(self.config.Feelpp.CommandLine.case.commands)

        # build scale commands with heatfluid exception handling
        if self.toolbox == 'heatfluid':
            scaleCommands = [   '--heat-fluid.scalability-save=1', '--heat-fluid.heat.scalability-save=1', '--heat-fluid.fluid.scalability-save=1']
        else:
            scaleCommands = [f'--{self.toolbox}.scalability-save=1']

        self.executable_opts.extend(scaleCommands)


    def findScaleFiles(self, keyword='scalibility', extension='.data'):
        pattern = os.path.join(self.feelOutputPath, f'*{keyword}*{extension}')
        files = glob.glob(pattern)
        return files


    @run_before('performance')
    def set_perf_vars(self):

        self.perf_variables = {}
        make_perf = sn.make_performance_function
        scaleFiles = self.findScaleFiles()
        for filePath in scaleFiles:
            names = self.get_column_names(filePath)
            perfNumber = len(names)
            line = self.extractLine(self.pattern_generator(perfNumber), filePath, perfNumber)

            perfStage = filePath.split('scalibility.')[-1].split('.data')[0]
            for i in range(perfNumber):
                unit = 's'
                if i == 0 and 'Solve' in perfStage:
                    unit = 'iter'
                self.perf_variables.update( {f'{perfStage}_{names[i]}' : make_perf(line[i], unit=unit)} )


    @sanity_function
    def checkers_success(self):
        notFailed = sn.assert_not_found(r'\\32m \[failure\] ', self.stdout)
        stopped = sn.assert_found(r'[ Stopping Feel++ ]', self.stdout)
        return notFailed and stopped