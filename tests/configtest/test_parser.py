""" Tests for parsing arguments """
import sys, os, tempfile
import pytest
from feelpp.benchmarking.reframe.parser import Parser
from unittest.mock import patch

def initParser(args):
    with patch('sys.argv', [''] + args):
        return Parser()


class TestParser:
    """ Tests for the Parser class"""

    def test_absolutePathConversion(self):
        """Checks that Parser paths arguments are converted to absolute paths successfully"""
        configs_dir = os.path.join(os.path.dirname(__file__),"../data/configs/")
        parser = initParser(['-mc',os.path.join(configs_dir,'mockMachineConfig.json'),'-bc',os.path.join(configs_dir,'mockAppConfig.json'),'-pc',os.path.join(configs_dir,'website_config.json')])

        assert parser.args.machine_config == os.path.abspath(os.path.join(configs_dir,"mockMachineConfig.json"))
        assert parser.args.benchmark_config == os.path.abspath(os.path.join(configs_dir,"mockAppConfig.json"))
        assert parser.args.plots_config == os.path.abspath(os.path.join(configs_dir,"website_config.json"))

    def test_validation(self):
        """ Tests that only valid argument combinations are supported
        checks that that the app exits for the following cases:
        -   No benchmark config and no dir provided
        - Both dir and benchmark config are provided
        -   No machine config is provided
        - The directory does not exist
        """

        with patch("sys.exit", side_effect=ValueError("sys exit called")):
            with pytest.raises(ValueError,match='sys exit called'):
                #No benchmark config
                parser = initParser(['-mc','machine_config.json','-pc','plots_config.json'])

            with pytest.raises(ValueError,match='sys exit called'):
                #No machine config
                parser = initParser(['-pc','plots_config.json','-bc','test_bc.json'])


