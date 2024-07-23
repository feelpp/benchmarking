import reframe                  as rfm
import reframe.core.runtime     as rt

import os


def parametrizeTaskNumber(minCpu, maxCpu, minNode, maxNode):
    for part in rt.runtime().system.partitions:
        nbTask = minCpu
        while (nbTask < part.processor.num_cpus) and (nbTask <= maxCpu):
            yield nbTask
            nbTask <<= 1

        if maxNode < part.devices[0].num_devices:
            nbNodes = maxNode
        else:
            nbNodes = part.devices[0].num_devices
        for i in range(minNode, nbNodes+1):
            nbTask = i * part.processor.num_cpus
            yield nbTask



@rfm.simple_test
class Setup(rfm.RunOnlyRegressionTest):

    valid_systems = ['*']
    valid_prog_environs = ['*']

    feelppdbPath = os.environ.get('FEELPP_OUTPUT_PREFIX')

    minCPU = int(os.environ.get('MIN_CPU'))
    maxCPU = int(os.environ.get('MAX_CPU'))
    minNodes = int(os.environ.get('MIN_NODES'))
    maxNodes = int(os.environ.get('MAX_NODES'))


    # Parametrization
    nbTask = parameter(parametrizeTaskNumber(minCPU, maxCPU, minNodes, maxNodes))


    @run_before('run')
    def setTaskNumber(self):
        self.num_tasks_per_node = min(self.nbTask, self.current_partition.processor.num_cpus)
        self.num_cpus_per_task = 1
        self.num_tasks = self.nbTask


    # Launcher options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core']