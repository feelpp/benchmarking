import reframe                  as rfm
import reframe.core.runtime     as rt
import reframe.utility.sanity   as sn
import os
import sys


root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
sys.path.insert(0, root)
from src.feelpp.benchmarking.configReader import ConfigReader

"""
print("TEST")
config = ConfigReader()
print("TEST")
"""

def parametrizeTaskNumber(minCPU, maxCPU, minNodes, maxNodes):

    for part in rt.runtime().system.partitions:
        nbTask = minCPU
        yield nbTask
        while (nbTask < part.processor.num_cpus) and (nbTask < maxCPU):
            nbTask <<= 1
            yield nbTask

        if not (minNodes == 1 and maxNodes == 1):
            if maxNodes < part.devices[0].num_devices:
                nbNodes = maxNodes
            else:
                nbNodes = part.devices[0].num_devices
            for i in range(minNodes+1, nbNodes+1):
                nbTask = i * part.processor.num_cpus
                yield nbTask



@rfm.simple_test
class Setup(rfm.RunOnlyRegressionTest):

    valid_systems = ['*']
    valid_prog_environs = ['*']

    feelppdbPath = os.environ.get('FEELPP_OUTPUT_PREFIX')
    feelpp_out_prefix = os.environ.get('FEELPP_OUTPUT_PREFIX')

    config = ConfigReader(mode="CpuVariation", configPath="./../../../../../benchConfig.json")

    # Parametrization
    """
    minCPU = int(os.environ.get('MIN_CPU'))
    maxCPU = int(os.environ.get('MAX_CPU'))
    minNodes = int(os.environ.get('MIN_NODES'))
    maxNodes = int(os.environ.get('MAX_NODES'))
    """

    minCPU = config.Reframe.Mode.topology.minPhysicalCpuPerNode
    maxCPU = config.Reframe.Mode.topology.maxPhysicalCpuPerNode
    minNodes = config.Reframe.Mode.topology.minNodeNumber
    maxNodes = config.Reframe.Mode.topology.maxNodeNumber
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


    # The following methods will be used in CpuVariation and ModelVariation
    def pattern_generator(self, valuesNumber):
        valPattern = '([0-9e\-\+\.]+)'
        linePattern = r'^\d+[\s]+' + rf'{valPattern}[\s]+' * valuesNumber
        linePattern = linePattern[:-1] + '*'
        return linePattern

    def extractLine(self, pattern, path, length, line=0):
        tags = range(1, length+1)
        if 'Solve' in path:
            convertion = [int] + [float]*(length-1)     # for ksp-niter conversion in int
        else:
            convertion = float
        lines = sn.extractall(pattern, path, tag=tags, conv=convertion)
        return lines[line]                              # to modify for unsteady cases