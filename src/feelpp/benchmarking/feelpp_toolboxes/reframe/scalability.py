import reframe.utility.sanity as sn

class ScalabilityHandler:
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory if scalability_config.directory[-1] != "/" else scalability_config.directory[:-1]
        self.stages = { stage["name"]:{k:v for k,v in stage if k != "name"} for stage in scalability_config.stages }
        self.perf_variables = {}

    def setFullPath(self):
        for stage_name, v in self.stages.items():
            self.stages[stage_name]["filepath"] = f"{self.directory}/{v.file}"

    def parsePerformanceFile(self,filepath):
        pass

    def setPerformanceVariables(self):
        pass