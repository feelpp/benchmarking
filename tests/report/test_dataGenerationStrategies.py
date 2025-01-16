import pytest
from feelpp.benchmarking.report.dataGenerationStrategies import DataGeneratorFactory, PlotlyGenerator, PlotlyHtmlGenerator, CsvGenerator, PgfGenerator
from test_transformationStrategies import PlotConfigMocker

class TestPlotlyGenerator:
    pass

class TestPlotlyHtmlGenerator:
    pass

class TestPgfGenerator:
    pass

class TestCsvGenerator:
    pass




@pytest.mark.parametrize(("format","expected_class"),[
    ("plotly",PlotlyGenerator),
    ("html",PlotlyHtmlGenerator),
    ("pgf",PgfGenerator),
    ("csv",CsvGenerator),
    ("unkown",None)
])
def testDataGeneratorFactory(format,expected_class):
    """ Tests the correct generation of DataGeneratorStrategy objects by the DataGeneratorFactory class """
    if expected_class:
        strat = DataGeneratorFactory.create(format)
        assert isinstance(strat,expected_class)
        assert hasattr(strat,"generate") and callable(strat.generate)
    else:
        with pytest.raises(NotImplementedError):
            strat = DataGeneratorFactory.create(format)
