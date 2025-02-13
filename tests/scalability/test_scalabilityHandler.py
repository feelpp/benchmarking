"""Tests for the feelpp.benchmarking.reframe.scalability module"""

import pytest
import tempfile, json
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler, CsvExtractor,TsvExtractor,JsonExtractor,Extractor,ExtractorFactory
import numpy as np

class StageMocker:
    def __init__(self,format="",filepath="",name="",variables_path=[],units={"*":"s"}):
        self.format = format
        self.filepath = filepath
        self.name = name
        self.variables_path = variables_path
        self.units = units

class CustomVariableMocker:
    def __init__(self, name="",columns=[],op="",unit="s"):
        self.name = name
        self.columns = columns
        self.op = op
        self.unit = unit

class ScalabilityMocker:
    def __init__(self, directory="",stages=[],custom_variables=[]):
        self.directory = directory
        self.stages = stages
        self.custom_variables = custom_variables


class TestExtractors:

    @staticmethod
    def buildCsvString(columns,values):
        """Helper function to create the content of a CSV from a list of columns and a list of values.
        Args:
            columns(list[str]): List of colum values
            values(list[list[any]]): List of lists containing the csv values
        Returns
            str: The built csv string
        """
        assert all(len(columns) == len(v) for v in values)
        return ",".join(columns) + "\n" + "\n".join([",".join([str(r) for r in row]) for row in values])


    @pytest.mark.parametrize(("values"),[
        ([[1,2,3]]), ([[1,2,3],[4,5,6]])
    ])
    def test_extractCsv(self,values):
        file = tempfile.NamedTemporaryFile()
        columns = ["col1","col2","col3"]
        with open(file.name,"w") as f:
            f.write(self.buildCsvString(columns,values))

        extractor = CsvExtractor(filepath=file.name,stage_name="",units={"*":"s"})
        perfvars = extractor.extract()
        for j,column in enumerate(columns):
            for i in range(len(values)):
                column_name = column if len(values) == 1 else f"{column}_{i}"
                assert perfvars[column_name].evaluate() == values[i][j]

        file.close()

    @staticmethod
    def buildTsvString(index, columns, values):
        assert len(columns) == len(values)
        tsv = "# nProc "+ "   ".join(columns) + "\n" + f"{index} " + "   ".join([str(v) for v in values]) + "\n"
        return tsv

    def test_extractTsv(self):
        """ Test performance variable extraction for special TSV files [WILL BE REMOVED]"""
        index = 32
        file = tempfile.NamedTemporaryFile()
        columns = ["col1","col2","col3"]
        values = [1,2.5,1e-5]
        with open(file.name,"w") as f:
            f.write(self.buildTsvString(index,columns,values=values))

        extractor = TsvExtractor(filepath=file.name,stage_name="file",index=index,units={"*":"s"})
        perfvars = extractor.extract()
        for i,col1 in enumerate(columns):
            assert perfvars[f"file_{col1}"].evaluate() == values[i]

        file.close()


    def test_extractJson(self):
        """ Test performance variable extraction for JSON files"""
        file = tempfile.NamedTemporaryFile()
        values = {
            "field1":0.5,
            "field2":{
                "field2_1":5,
                "field2_2":{
                    "field2_2_1":1,
                    "field2_2_2":3,
                }
            }
        }
        with open(file.name,"w") as f:
            json.dump(values,f)

        #Test no variables path
        extractor = JsonExtractor(file.name,"",units={"*":"s"},variables_path=[])
        perfvars = extractor.extract()
        assert perfvars == {}


        #Test with *
        extractor = JsonExtractor(file.name,"",units={"*":"s"},variables_path=["*"])
        perfvars = extractor.extract()
        for k,v in perfvars.items():
            path = k.split(".")
            dic = values
            for p in path:
                dic = dic[p]
            val = dic
            assert val == v.evaluate()

        #Test with specific paths
        extractor = JsonExtractor(file.name,"",units={"*":"s"},variables_path=["field2.field2_2.*","field1"])
        perfvars = extractor.extract()
        assert len(perfvars.keys()) == 3
        assert perfvars["field1"].evaluate() == values["field1"]
        assert perfvars["field2_2_1"].evaluate() == values["field2"]["field2_2"]["field2_2_1"]
        assert perfvars["field2_2_2"].evaluate() == values["field2"]["field2_2"]["field2_2_2"]

        file.close()

        #Test with multiple wildcards
        file = tempfile.NamedTemporaryFile()
        values = {
            "hardware": {
                "gaya3": {
                    "mem": {
                        "available": {
                            "host": "527759648",
                            "physical": "442275",
                            "virtual": "51059"
                        },
                        "total": {
                            "host": "527759648",
                            "physical": "515390",
                            "virtual": "51199"
                        }
                    }
                },
                "gaya2":{
                    "mem": {
                        "available": {
                            "host": "101010101",
                            "physical": "442275",
                        },
                        "total": {
                            "host": "202020202",
                            "physical": "515390",
                            "virtual": "51199"
                        }
                    }
                }
            }
        }
        with open(file.name,"w") as f:
            json.dump(values,f)


        extractor = JsonExtractor(file.name,"",variables_path=["hardware.*.mem.*.host"],units={"*":"s"})
        perfvars = extractor.extract()
        assert perfvars["gaya2.available"] == values["hardware"]["gaya2"]["mem"]["available"]["host"]
        assert perfvars["gaya2.total"] == values["hardware"]["gaya2"]["mem"]["total"]["host"]
        assert perfvars["gaya3.available"] == values["hardware"]["gaya3"]["mem"]["available"]["host"]
        assert perfvars["gaya3.total"] == values["hardware"]["gaya3"]["mem"]["total"]["host"]



        extractor = JsonExtractor(file.name,"",variables_path=["hardware.*.mem.*"],units={"*":"s"})
        perfvars = extractor.extract()
        assert perfvars["gaya2.available.host"] == values["hardware"]["gaya2"]["mem"]["available"]["host"]
        assert perfvars["gaya2.available.physical"] == values["hardware"]["gaya2"]["mem"]["available"]["physical"]
        assert perfvars["gaya2.total.host"] == values["hardware"]["gaya2"]["mem"]["total"]["host"]
        assert perfvars["gaya2.total.physical"] == values["hardware"]["gaya2"]["mem"]["total"]["physical"]

        assert perfvars["gaya3.available.host"] == values["hardware"]["gaya3"]["mem"]["available"]["host"]
        assert perfvars["gaya3.available.physical"] == values["hardware"]["gaya3"]["mem"]["available"]["physical"]
        assert perfvars["gaya3.available.virtual"] == values["hardware"]["gaya3"]["mem"]["available"]["virtual"]
        assert perfvars["gaya3.total.host"] == values["hardware"]["gaya3"]["mem"]["total"]["host"]
        assert perfvars["gaya3.total.physical"] == values["hardware"]["gaya3"]["mem"]["total"]["physical"]
        assert perfvars["gaya3.total.virtual"] == values["hardware"]["gaya3"]["mem"]["total"]["virtual"]

        file.close()


class TestScalabilityHandler:


    @pytest.mark.parametrize(("op","fct"),[
        ("sum",sum),
        ("min",min),
        ("max",max),
        ("mean",lambda l: sum(l)/len(l))
    ])
    def test_aggregateCustomVar(self,op,fct):
        """ Tests that aggregation functions are correclty computed"""
        values = np.random.uniform(100,100,50).tolist()
        aggregated = ScalabilityHandler.aggregateCustomVar(op,values)
        assert aggregated == fct(values)

    def test_unkownAggregateCustomVar(self):
        """ Checks that a NotImplementedError is raised for unkown operations"""
        with pytest.raises(NotImplementedError):
            ScalabilityHandler.aggregateCustomVar("unkown",[1,2,3])


    def test_evaluateCustomVariables(self):
        """ Tests the manipulation of custom performance variables, built using existing variables. """

        index = 32
        file = tempfile.NamedTemporaryFile()
        columns = ["col1","col2","col3"]
        values = [1,2,5.5]
        with open(file.name,"w") as f:
            f.write(TestExtractors.buildTsvString(index,columns,values=values))

        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="tsv",filepath=file.name,name=""),
            ],
            custom_variables=[
                CustomVariableMocker(name="custom_var",columns=["col1","col3"],op="sum",unit="CUSTOM_UNIT")
            ]
        ))
        perf_vars = scalability_handler.getPerformanceVariables(index)
        perf_vars.update(scalability_handler.getCustomPerformanceVariables(perf_vars))

        assert perf_vars["custom_var"].evaluate() == 6.5
        assert perf_vars["custom_var"].unit == "CUSTOM_UNIT"

        #Testing recursive custom variables

        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="tsv",filepath=file.name,name=""),
            ],
            custom_variables=[
                CustomVariableMocker(name="custom_var1",columns=["col1","col3"],op="sum",unit="CUSTOM_UNIT"),
                CustomVariableMocker(name="custom_var2",columns=["col1","col2"],op="max",unit="CUSTOM_UNIT"),
                CustomVariableMocker(name="recursive_var",columns=["custom_var1","custom_var2","col1"],op="mean",unit="CUSTOM_UNIT"),
                CustomVariableMocker(name="re_recursive_var",columns=["recursive_var","custom_var2","col3"],op="sum",unit="CUSTOM_UNIT"),
            ]
        ))
        perf_vars = scalability_handler.getPerformanceVariables(index)
        perf_vars.update(scalability_handler.getCustomPerformanceVariables(perf_vars))

        assert perf_vars["custom_var1"].evaluate() == 6.5
        assert perf_vars["custom_var2"].evaluate() == 2
        assert perf_vars["recursive_var"].evaluate() == (6.5+2+1)/3
        assert perf_vars["recursive_var"].unit == "CUSTOM_UNIT"
        assert perf_vars["re_recursive_var"].evaluate() == perf_vars["recursive_var"].evaluate() + perf_vars["custom_var2"].evaluate() + perf_vars["col3"].evaluate()


        file.close()