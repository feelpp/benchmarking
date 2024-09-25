import os
import shutil
import glob
import reframe                  as rfm
import reframe.utility.sanity   as sn
from setup                      import Setup

@rfm.simple_test
class ToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'

    toolbox = variable(str, value='')
    case = variable(str, value='')
    #physical_values_path = variable(str, value='')


    @run_after('init')
    def setVariables(self):
        self.toolbox = self.config.feelpp.toolbox
        self.case = self.config.feelpp.commandLine.configFilesToStr()

    @run_after('init')
    def buildPaths(self):
        # Extends output path with 'np_{task_number}'
        self.feel_output_suffix = os.path.join(self.config.feelpp.commandLine.repository.case, f'np_{self.nb_task}')
        self.feel_output_path = os.path.join(self.config.feelpp.commandLine.repository.prefix, f'{self.feel_output_suffix}')
        #self.physical_values_path = os.path.join(self.feel_output_path, f'{self.toolbox}.measures/values.csv')


    @run_before('run')
    def cleanFolder(self):
        if os.path.exists(self.feel_output_path):
            print(" >>> Cleaning Feelpp output folder...")
            shutil.rmtree(self.feel_output_path)
        else:
            print(" >>> New folder will be created...")


    @run_before('run')
    def set_executable_opts(self):

        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-files {self.case}',
                                f'--repository.prefix {self.config.feelpp.commandLine.repository.prefix}',
                                f'--repository.case {self.feel_output_suffix}',
                                '--fail-on-unknown-option 1']

        # json commands needs the '--toolbox' prefix,
        if self.config.feelpp.commandLine.json.commands:
            # scale files for heatfluid are named 'heat-fluid'
            toolbox = 'heat-fluid' if self.toolbox == 'heatfluid' else self.toolbox
            for cmd in self.config.feelpp.commandLine.json.commands:
                cmd = f'--{toolbox}.' + cmd
                self.executable_opts.append(cmd)

        if self.config.feelpp.commandLine.case.commands:
            self.executable_opts.extend(self.config.feelpp.commandLine.case.commands)

        # build scale commands with heatfluid exception handling
        if self.toolbox == 'heatfluid':
            scale_commands = [   '--heat-fluid.scalability-save=1', '--heat-fluid.heat.scalability-save=1', '--heat-fluid.fluid.scalability-save=1']
        else:
            scale_commands = [f'--{self.toolbox}.scalability-save=1']

        self.executable_opts.extend(scale_commands)


    def findScaleFiles(self, keyword='scalibility', extension='.data'):
        pattern = os.path.join(self.feel_output_path, f'*{keyword}*{extension}')
        files = glob.glob(pattern)
        return files


    @run_before('performance')
    def set_perf_vars(self):

        self.perf_variables = {}
        make_perf = sn.make_performance_function
        scale_files = self.findScaleFiles()
        for file_path in scale_files:
            names = self.get_column_names(file_path)
            perf_number = len(names)
            line = self.extractLine(self.pattern_generator(perf_number), file_path, perf_number)

            perf_stage = file_path.split('scalibility.')[-1].split('.data')[0]
            for i in range(perf_number):
                unit = 's'
                if i == 0 and 'Solve' in perf_stage:
                    unit = 'iter'
                self.perf_variables.update( {f'{perf_stage}_{names[i]}' : make_perf(line[i], unit=unit)} )


    @sanity_function
    def checkers_success(self):
        not_failed = sn.assert_not_found(r'\\32m \[failure\] ', self.stdout)
        stopped = sn.assert_found(r'[ Stopping Feel++ ]', self.stdout)
        return not_failed and stopped