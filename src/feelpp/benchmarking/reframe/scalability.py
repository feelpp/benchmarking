import reframe.utility.sanity as sn
import os, re,json

class ScalabilityHandler:
    """ Class to handle scalability related attributes"""
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory
        self.stages =  scalability_config.stages
        self.custom_variables = scalability_config.custom_variables
        self.filepaths = {k.name if k.name else k.file : os.path.join(self.directory,k.file) for k in self.stages}

    def getPerformanceVariables(self,index):
        """ Opens and parses the performance variable values depending on the config setup.
        Args:
            index (numerical | string). Key/index to find in the scalability file, depending on the format.
            e.g. If a csv file is provided, and index=32. Only the row with nProcs==32 is retrieved.
        """
        perf_variables = {}
        for stage in self.stages:
            if stage.format == "csv":
                pass
            elif stage.format == "tsv":
                #WARNING: This assumes that index is in column 0
                with open(self.filepaths[stage.name if stage.name else stage.file],"r") as f:
                    lines = f.readlines()

                columns = re.sub("\s+"," ",lines[0].replace("# ","")).strip().split(" ")

                vars = sn.extractall_s(
                    patt=rf'^{index}[\s]+' + r'([0-9e\-\+\.]+)[\s]+'*(len(columns)-1),
                    string="\n".join(lines[1:]),
                    conv=float,
                    tag=range(1,len(columns))
                )[0]


                for i, col in enumerate(columns[1:]): #UNIT TEMPORARY HOTFIX
                    perf_variables.update( { f"{stage.name}_{col}" if stage.name else col: sn.make_performance_function(vars[i],unit="iter" if col.endswith("-niter") else "s")  })
            elif stage.format == "json":
                splitted_keys = stage.variables_path.split("*")

                if len(splitted_keys) != 2:
                    raise NotImplementedError(f"More than one wildcard is not supported. Number of wildcards: {len(splitted_keys)}")

                left_keys = splitted_keys[0].strip(".").split(".")
                right_keys = splitted_keys[1].strip(".").split(".")

                with open(self.filepaths[stage.name if stage.name else stage.file],"r") as f:
                    j = json.load(f)

                for left_key in left_keys:
                    if left_key:
                        j = j[left_key]

                wildcards = j.keys()
                fields = {}
                for wildcard in wildcards:
                    fields[wildcard] = j[wildcard]
                    for right_key in right_keys:
                        if right_key:
                            fields[wildcard] = fields[wildcard][right_key]

                for k,v in fields.items():
                    perf_variables.update( {
                        f"{stage.name}_{k}" if stage.name else k
                        : sn.make_performance_function(sn.defer(v),unit="s")
                    })

            else:
                raise NotImplementedError

        return perf_variables

    def getCustomPerformanceVariables(self,perfvars):
        custom_perfvars = {}
        for custom_var in self.custom_variables:

            custom_var_value = [
                perfvars[col].evaluate()
                for col in custom_var.columns
            ]

            if custom_var.op == "sum":
                custom_var_value = sum(custom_var_value)
            elif custom_var.op == "min":
                custom_var_value = min(custom_var_value)
            elif custom_var.op =="max":
                custom_var_value = max(custom_var_value)
            elif custom_var.op == "mean":
                custom_var_value = sum(custom_var_value)/len(custom_var_value)
            else:
                raise NotImplementedError(f"Operation {custom_var.op} is not implemented")

            custom_perfvars[custom_var.name] = sn.make_performance_function(sn.defer(custom_var_value),unit=custom_var.unit)

        return custom_perfvars