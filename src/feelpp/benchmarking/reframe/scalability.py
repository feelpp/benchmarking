import reframe.utility.sanity as sn
import os, re,json
from feelpp.benchmarking.reframe.config.configReader import TemplateProcessor


#TODO: Factor this with outputs. Consider strategy pattern for formats
class ScalabilityHandler:
    """ Class to handle scalability related attributes"""
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory
        self.stages =  scalability_config.stages
        self.custom_variables = scalability_config.custom_variables
        self.filepaths = {k.name if k.name else k.filepath : os.path.join(self.directory,k.filepath) for k in self.stages}

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
                with open(self.filepaths[stage.name if stage.name else stage.filepath],"r") as f:
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
                for varpath in stage.variables_path:
                    splitted_keys = varpath.split("*")

                    if len(splitted_keys) > 2:
                        raise NotImplementedError(f"More than one wildcard is not supported. Number of wildcards: {len(splitted_keys)}")

                    left_keys = splitted_keys[0].strip(".").split(".")


                    with open(self.filepaths[stage.name if stage.name else stage.filepath],"r") as f:
                        j = json.load(f)

                    for left_key in left_keys:
                        if left_key:
                            j = j[left_key]

                    fields = {}
                    if len(splitted_keys) == 1:
                        fields[left_keys[-1]] = j
                    else:
                        right_keys = splitted_keys[1].strip(".").split(".")

                        wildcards = j.keys()
                        for wildcard in wildcards:
                            fields[wildcard] = j[wildcard]
                            for right_key in right_keys:
                                if right_key:
                                    fields[wildcard] = fields[wildcard][right_key]

                    fields = TemplateProcessor.flattenDict(fields)

                    for k,v in fields.items():
                        perf_variables.update( {
                            f"{stage.name}_{k}" if stage.name else k
                            : sn.make_performance_function(sn.defer(v),unit="s")
                        })

            else:
                raise NotImplementedError

        return perf_variables

    @staticmethod
    def aggregateCustomVar(op,column_values):
        if op == "sum":
            return sum(column_values)
        elif op == "min":
            return min(column_values)
        elif op =="max":
            return max(column_values)
        elif op == "mean":
            return sum(column_values)/len(column_values)
        else:
            raise NotImplementedError(f"Operation {op} is not implemented")


    def getCustomPerformanceVariables(self,perfvars):
        """ Creates custom aggregated performance variables from existing ones
        Args:
            perfvars dict(str,sn.deferrable function): Existing performance variables to use for extraction

        Returns:
            dict(str,sn.deferrable function) Dictionnary containing only the custom performance variables
        """
        custom_perfvars = {}

        computed_vars = {}


        def evaluateCustomVariable(custom_var):

            if custom_var.name in computed_vars:
                return computed_vars[custom_var.name]

            column_values = []
            for col in custom_var.columns:
                if col in perfvars:
                    column_values.append(perfvars[col].evaluate())
                elif col in custom_perfvars:
                    column_values.append(evaluateCustomVariable(custom_perfvars[col]))
                else:
                    raise ValueError(f"Custom variable not found : {custom_var.name}")

            custom_var_value = self.aggregateCustomVar(custom_var.op,column_values)
            computed_vars[custom_var.name] = custom_var_value
            return custom_var_value



        for custom_var in self.custom_variables:
            custom_perfvars[custom_var.name] = sn.make_performance_function(
                sn.defer(evaluateCustomVariable(custom_var)),unit=custom_var.unit
            )

        return custom_perfvars