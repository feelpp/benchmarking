import reframe.utility.sanity as sn
import os, re

class ScalabilityHandler:
    """ Class to handle scalability related attributes"""
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory
        self.stages =  scalability_config.stages
        self.filepaths = {k.name: os.path.join(self.directory,k.file) for k in self.stages}

    def cleanupScalabilityFiles(self):
        """ Deletes scalability files based on the provided filepaths. Should be run before the init step of a reframe test """
        for filepath in self.filepaths.values():
            if os.path.exists(filepath):
                os.remove(filepath)

    def getPerformanceVariables(self,index):
        """ Opens and parses the performance variable values depending on the config setup.
        Args:
            index (numerical | string). Key/index to find in the scalability file, depending on the format.
            e.g. If a csv file is provided, and index=32. Only the row with nProcs==32 is retrieved.
        """
        perf_variables = {}
        for stage in self.stages:
            match stage.format:
                case "csv":
                    pass
                case "tsv":
                    #WARNING: This assumes that index is in column 0
                    with open(self.filepaths[stage.name],"r") as f:
                        lines = f.readlines()

                    columns = re.sub("\s+"," ",lines[0].replace("# ","")).strip().split(" ")

                    vars = sn.extractall_s(
                        patt=rf'^{index}[\s]+' + r'([0-9e\-\+\.]+)[\s]+'*(len(columns)-1),
                        string="\n".join(lines[1:]),
                        conv=float,
                        tag=range(1,len(columns))
                    )[0]


                    for i, col in enumerate(columns[1:]): #UNIT TEMPORARY HOTFIX
                        perf_variables.update( { f"{stage.name}_{col}" : sn.make_performance_function(vars[i],unit="item" if col.endswith("-niter") else "s")  })

                case _:
                    raise NotImplementedError

        return perf_variables