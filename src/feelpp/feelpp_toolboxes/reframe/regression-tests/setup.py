import os
import sys
import reframe                  as rfm
import reframe.core.runtime     as rt
import reframe.utility.sanity   as sn
from feelpp.benchmarking.configReader import ConfigReader


def parametrizeTaskNumber(min_cpu, max_cpu, min_nodes, max_nodes):

    for part in rt.runtime().system.partitions:
        nb_task = min_cpu
        yield nb_task
        while (nb_task < part.processor.num_cpus) and (nb_task < max_cpu):
            nb_task <<= 1
            yield nb_task

        if not (min_nodes == 1 and max_nodes == 1):
            if max_nodes < part.devices[0].num_devices:
                nb_nodes = max_nodes
            else:
                nb_nodes = part.devices[0].num_devices
            for i in range(min_nodes+1, nb_nodes+1):
                nb_task = i * part.processor.num_cpus
                yield nb_task


@rfm.simple_test
class Setup(rfm.RunOnlyRegressionTest):

    valid_systems = ['*']
    valid_prog_environs = ['*']

    workdir = os.environ['WORKDIR']

    config_path = variable(str, value=os.environ['CONFIG_PATH'])
    config = ConfigReader(str(config_path))

    min_cpu = config.reframe.mode.topology.min_physical_cpus_per_node
    max_cpu = config.reframe.mode.topology.max_physical_cpus_per_node
    min_nodes = config.reframe.mode.topology.min_node_number
    max_nodes = config.reframe.mode.topology.max_node_number

    nb_task = parameter(parametrizeTaskNumber(min_cpu, max_cpu, min_nodes, max_nodes))

    @run_before('run')
    def setTaskNumber(self):
        self.num_tasks_per_node = min(self.nb_task, self.current_partition.processor.num_cpus)
        self.num_cpus_per_task = 1
        self.num_tasks = self.nb_task

    @run_after('init')
    def setEnvVars(self):
        self.env_vars['OMP_NUM_THREADS'] = 1

    @run_after('init')
    def setTags(self):
        self.tags = {
            "is_partial",
            self.config.Feelpp.testCase,
            os.environ.get("EXEC_POLICY","serial")
        }


    # Set scheduler and launcher options
    @run_before('run')
    def setLaunchOptions(self):
        self.exclusive_access = self.config.reframe.mode.exclusive_access
        self.job.launcher.options = ['-bind-to core']

    def get_column_names(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                if line.startswith('# nProc'):
                    header = line.strip().split()
                    return header[2:]               # exclude '# nProc'
        return []

    def pattern_generator(self, values_number):
        val_pattern = '([0-9e\-\+\.]+)'
        line_pattern = r'^\d+[\s]+' + rf'{val_pattern}[\s]+' * values_number
        line_pattern = line_pattern[:-1] + '*'
        return line_pattern

    def extractLine(self, pattern, path, length, line=0):
        tags = range(1, length+1)
        if 'Solve' in path:
            convertion = [int] + [float]*(length-1)     # for ksp-niter conversion in int
        else:
            convertion = float
        lines = sn.extractall(pattern, path, tag=tags, conv=convertion)
        return lines[line]                              # to modify for unsteady cases