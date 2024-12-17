"""Tests for the feelpp.benchmarking.reframe.scalability module"""

import pytest
import tempfile, json
from feelpp.benchmarking.reframe.scalability import ScalabilityHandler
from unittest.mock import patch
import numpy as np

class StageMocker:
    def __init__(self,format="",filepath="",name="",variables_path=[]):
        self.format = format
        self.filepath = filepath
        self.name = name
        self.variables_path = variables_path

class ScalabilityMocker:
    def __init__(self, directory="",stages=[],custom_variables=[]):
        self.directory = directory
        self.stages = stages
        self.custom_variables = custom_variables


class TestScalabilityHandler:

    def test_extractCsv(self):
        """ Test performance variable extraction for CSV files"""
        pass

    def test_extractTsv(self):
        """ Test performance variable extraction for special TSV files [WILL BE REMOVED]"""

        def buildTsvString(index, columns, values):
            assert len(columns) == len(values)
            tsv = "# nProc "+ "   ".join(columns) + "\n" + f"{index} " + "   ".join([str(v) for v in values]) + "\n"
            return tsv

        index = 32
        file1 = tempfile.NamedTemporaryFile()
        columns1 = ["col1","col2","col3"]
        values1 = [1,2.5,1e-5]
        with open(file1.name,"w") as f:
            f.write(buildTsvString(index,columns1,values=values1))

        file2 = tempfile.NamedTemporaryFile()
        columns2 = ["col1","colX"]
        values2 = [4,5.5]
        with open(file2.name,"w") as f:
            f.write(buildTsvString(index,columns2,values2))

        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="tsv",filepath=file1.name,name="file1"),
                StageMocker(format="tsv",filepath=file2.name,name="file2")
            ]
        ))

        perf_vars = scalability_handler.getPerformanceVariables(index)
        for i,col1 in enumerate(columns1):
            print(perf_vars["file1_"+col1])
            assert perf_vars[f"file1_{col1}"].evaluate() == values1[i]

        for j,col2 in enumerate(columns2):
            assert perf_vars[f"file2_{col2}"].evaluate() == values2[j]

        file1.close()
        file2.close()


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
        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="json",filepath=file.name,name=""),
            ]
        ))
        perf_vars = scalability_handler.getPerformanceVariables(None)
        assert perf_vars == {}


        #Test with *
        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="json",filepath=file.name,name="",variables_path=["*"]),
            ]
        ))
        perf_vars = scalability_handler.getPerformanceVariables(None)
        for k,v in perf_vars.items():
            path = k.split(".")
            dic = values
            for p in path:
                dic = dic[p]
            val = dic
            assert val == v.evaluate()

        #Test with specific paths
        scalability_handler = ScalabilityHandler(ScalabilityMocker(
            directory="",
            stages = [
                StageMocker(format="json",filepath=file.name,name="",variables_path=["field2.field2_2.*","field1"]),
            ]
        ))
        perf_vars = scalability_handler.getPerformanceVariables(None)
        assert len(perf_vars.keys()) == 3
        assert perf_vars["field1"].evaluate() == values["field1"]
        assert perf_vars["field2_2_1"].evaluate() == values["field2"]["field2_2"]["field2_2_1"]
        assert perf_vars["field2_2_2"].evaluate() == values["field2"]["field2_2"]["field2_2_2"]

        file.close()



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

        pass