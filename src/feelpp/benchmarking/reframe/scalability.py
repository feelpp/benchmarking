import reframe.utility.sanity as sn
import os, re,json
from feelpp.benchmarking.reframe.config.configReader import TemplateProcessor


class Extractor:
    def __init__(self,filepath,stage_name):
        self.filepath = filepath
        self.stage_name = stage_name
        self.unit = "s"

    def extract(self):
        raise NotImplementedError("Not to be called directly from Extractor base class")


class TsvExtractor(Extractor):
    def __init__(self,filepath,stage_name,index):
        super().__init__(filepath,stage_name)
        self.index = index

    def _getFileContent(self):
        with open(self.filepath,"r") as f:
            content = f.readlines()
        return content

    def _extractVariables(self,content):
        #WARNING: This assumes that index is in column 0
        columns = re.sub("\s+"," ",content[0].replace("# ","")).strip().split(" ")

        vars = sn.extractall_s(
            patt=rf'^{self.index}[\s]+' + r'([0-9e\-\+\.]+)[\s]+'*(len(columns)-1),
            string="\n".join(content[1:]),
            conv=float,
            tag=range(1,len(columns))
        )[0]

        return columns,vars


    def _getPerfVars(self,columns,vars):
        perf_variables = {}
        for i, col in enumerate(columns[1:]): #UNIT TEMPORARY HOTFIX
            perfvar_name = f"{self.stage_name}_{col}" if self.stage_name else col
            perf_variables[perfvar_name] = sn.make_performance_function(vars[i],unit="iter" if col.endswith("-niter") else self.unit)

        return perf_variables


    def extract(self):
        content = self._getFileContent()
        columns,vars = self._extractVariables(content)
        return self._getPerfVars(columns,vars)

class CsvExtractor(Extractor):
    def __init__(self, filepath, stage_name):
        super().__init__(filepath, stage_name)

    def _extractVariables(self):
        number_regex = re.compile(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$')
        rows = sn.extractall(
            r'^(?!\s*$)(.*?)[\s\r\n]*$',
            self.filepath,
            0,
            conv=lambda x: [float(col.strip()) if number_regex.match(col.strip()) else col.strip() for col in x.split(',') if col.strip()]
        )
        header = rows[0]
        rows = rows[1:]

        assert all ( len(header.evaluate()) == len(row) for row in rows), f"CSV File {self.filepath} is incorrectly formatted"
        return header,rows

    def _getPerfVars(self,columns,vars):
        perf_variables = {}
        nb_rows = len(vars.evaluate())
        for line in range(nb_rows):
            for i,col in enumerate(columns):
                perfvar_name = f"{self.stage_name}_{col}" if self.stage_name else col
                if nb_rows > 1:
                    perfvar_name = f"{perfvar_name}_{line}"
                perf_variables[perfvar_name] = sn.make_performance_function(vars[line][i],unit=self.unit)

        return perf_variables

    def extract(self):
        header,rows = self._extractVariables()
        return self._getPerfVars(header,rows)


class JsonExtractor(Extractor):
    def __init__(self, filepath, stage_name, variables_path):
        super().__init__(filepath, stage_name)
        self.variables_path = variables_path

    def _getFileContent(self):
        with open(self.filepath,"r") as f:
            content = json.load(f)
        return content

    def _extractVariables(self,content,varpath):
        splitted_keys = varpath.split("*")

        if len(splitted_keys) > 2:
            raise NotImplementedError(f"More than one wildcard is not supported. Number of wildcards: {len(splitted_keys)}")

        left_keys = splitted_keys[0].strip(".").split(".")

        j = content.copy()
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

        return fields.items()

    def _getPerfVars(self,items):
        perf_variables = {}
        for k,v in items:
            perfvar_name = f"{self.stage_name}_{k}" if self.stage_name else k
            perf_variables[perfvar_name] = sn.make_performance_function(sn.defer(v),unit=self.unit)

        return perf_variables


    def extract(self):
        content = self._getFileContent()
        perf_variables = {}
        for varpath in self.variables_path:
            items= self._extractVariables(content,varpath)
            perf_variables.update(self._getPerfVars(items))
        return perf_variables

class ScalabilityHandler:
    """ Class to handle scalability related attributes"""
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory
        self.stages =  scalability_config.stages
        self.custom_variables = scalability_config.custom_variables
        self.filepaths = {k.name if k.name else k.filepath : os.path.join(self.directory,k.filepath) for k in self.stages}

    def getPerformanceVariables(self,index=None):
        """ Opens and parses the performance variable values depending on the config setup.
        Args:
            index (numerical | string). Key/index to find in the scalability file, depending on the format.
            e.g. If a csv file is provided, and index=32. Only the row with nProcs==32 is retrieved.
        """
        perf_variables = {}
        for stage in self.stages:
            filepath = self.filepaths[stage.name if stage.name else stage.filepath]
            if stage.format == "csv":
                extractor = CsvExtractor(filepath=filepath, stage_name = stage.name)
            elif stage.format == "tsv":
                extractor = TsvExtractor(filepath=filepath,stage_name = stage.name,index=index)
            elif stage.format == "json":
                extractor = JsonExtractor(filepath=filepath,stage_name = stage.name, variables_path=stage.variables_path)
            else:
                raise NotImplementedError
            perf_variables.update( extractor.extract() )

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
                    column_values.append(custom_perfvars[col])
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