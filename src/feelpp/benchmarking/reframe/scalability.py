import reframe.utility.sanity as sn
import os, re,json
from feelpp.benchmarking.reframe.config.configReader import TemplateProcessor


class Extractor:
    def __init__(self,filepath,stage_name, units):
        self.filepath = filepath
        self.stage_name = stage_name
        self.units = units

    def _getPerfVars(self,columns,vars):
        perf_variables = {}
        nb_rows = len(vars.evaluate())
        for line in range(nb_rows):
            for i, col in enumerate(columns):
                perfvar_name = f"{self.stage_name}_{col}" if self.stage_name else col
                if nb_rows > 1:
                    perfvar_name = f"{perfvar_name}_{line}"
                perf_variables[perfvar_name] = sn.make_performance_function(vars[line][i],unit=self.units.get(col,self.units["*"]))

        return perf_variables

    def _extractVariables(self):
        raise NotImplementedError("Not to be called from base class")

    def extract(self):
        columns,vars = self._extractVariables()
        return self._getPerfVars(columns,vars)

class TsvExtractor(Extractor):
    def __init__(self,filepath,stage_name,units,index):
        super().__init__(filepath,stage_name,units)
        self.index = index

    def _getFileContent(self):
        with open(self.filepath,"r") as f:
            content = f.readlines()
        return content

    def _extractVariables(self):
        content = self._getFileContent()
        #WARNING: This assumes that index is in column 0
        columns = re.sub("\s+"," ",content[0].replace("# ","")).strip().split(" ")
        vars = sn.extractall_s(
            patt=rf'^{self.index}[\s]+' + r'([0-9e\-\+\.]+)[\s]+'*(len(columns)-1),
            string="\n".join(content[1:]),
            conv=float,
            tag=range(1,len(columns))
        )[0]
        return columns[1:],sn.defer([vars])


class CsvExtractor(Extractor):
    def __init__(self, filepath, stage_name, units):
        super().__init__(filepath, stage_name, units)

    def _extractVariables(self):
        number_regex = re.compile(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$')
        vars = sn.extractall(
            r'^(?!\s*$)(.*?)[\s\r\n]*$',
            self.filepath,
            0,
            conv=lambda x: [float(col.strip()) if number_regex.match(col.strip()) else col.strip() for col in x.split(',') if col.strip()]
        )
        columns = vars[0]
        vars = vars[1:]
        assert all ( len(columns.evaluate()) == len(row) for row in vars), f"CSV File {self.filepath} is incorrectly formatted"
        return columns,vars


class JsonExtractor(Extractor):
    def __init__(self, filepath, stage_name, units, variables_path):
        super().__init__(filepath, stage_name, units)
        self.variables_path = variables_path

    def _getFileContent(self):
        with open(self.filepath,"r") as f:
            content = json.load(f)
        return content

    def _recursiveExtract(self,varpath, content, fields=None, prefix=""):
        """ Extract values from a dictionary following a path (varpath) containing multiple wildcards"""
        if fields is None:
            fields = {}

        splitted_keys = varpath.split("*", 1)
        left_keys = splitted_keys[0].strip(".").split(".")

        j = content
        for left_key in left_keys:
            if left_key:
                j = j[left_key]

        if len(splitted_keys) == 1:
            fields[left_keys[-1]] = j
        else:
            right_keys = splitted_keys[1].strip(".")
            if "*" in right_keys:
                for wildcard, subcontent in j.items():
                    self._recursiveExtract(right_keys, subcontent, fields, prefix=f"{prefix}{wildcard}.")
            else:
                right_keys = right_keys.split(".")
                for wildcard, subcontent in j.items():
                    value = subcontent
                    for right_key in right_keys:
                        if right_key:
                            value = value[right_key]
                    fields[f"{prefix}{wildcard}"] = value

        return fields

    def _extractVariables(self):
        items = {}
        content = self._getFileContent()
        for varpath in self.variables_path:
            fields = self._recursiveExtract(varpath,content)
            fields = TemplateProcessor.flattenDict(fields)
            items.update(fields)
        return items.keys(),sn.defer([[sn.defer(v) for v in items.values()]])


class ExtractorFactory:
    """Factory class for extractor strategies"""
    @staticmethod
    def create(stage,directory,index=None):
        filepath = os.path.join(directory,stage.filepath)
        if stage.format == "csv":
            return CsvExtractor(filepath=filepath, stage_name = stage.name, units=stage.units)
        elif stage.format == "tsv":
            return TsvExtractor(filepath=filepath,stage_name = stage.name,index=index, units=stage.units)
        elif stage.format == "json":
            return JsonExtractor(filepath=filepath,stage_name = stage.name, variables_path=stage.variables_path, units=stage.units)
        else:
            raise NotImplementedError


class ScalabilityHandler:
    """ Class to handle scalability related attributes"""
    def __init__(self,scalability_config):
        self.directory = scalability_config.directory
        self.stages =  scalability_config.stages
        self.custom_variables = scalability_config.custom_variables

    def getPerformanceVariables(self,index=None):
        """ Opens and parses the performance variable values depending on the config setup.
        Args:
            index (numerical | string). Key/index to find in the scalability file, depending on the format.
            e.g. If a csv file is provided, and index=32. Only the row with nProcs==32 is retrieved.
        """
        perf_variables = {}
        for stage in self.stages:
            extractor = ExtractorFactory.create(stage,self.directory,index)
            perf_variables.update( extractor.extract() )

        return perf_variables

    @staticmethod
    def aggregateCustomVar(op,column_values):
        ops = {
            "sum":sum,
            "min":min,
            "max":max,
            "mean": lambda v : sum(v)/len(v)
        }
        if op not in ops:
            raise NotImplementedError(f"Operation {op} is not implemented")
        return ops[op](column_values)

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