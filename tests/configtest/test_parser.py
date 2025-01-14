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
        parser = initParser(['-mc','machine_config.json','-bc','benchmark_config.json','-pc','plots_config.json'])

        assert parser.args.machine_config == os.path.abspath("machine_config.json")
        assert parser.args.benchmark_config == [os.path.abspath("benchmark_config.json")]
        assert parser.args.plots_config == os.path.abspath("plots_config.json")

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
                #No benchmark config and no dir
                parser = initParser(['-mc','machine_config.json','-pc','plots_config.json'])

            with pytest.raises(ValueError,match='sys exit called'):
                #two dir and one bench config
                parser = initParser(['-mc','machine_config.json','-pc','plots_config.json','--dir','tests/configtest','--dir','tests/data','-bc','test_bc.json'])

            with pytest.raises(ValueError,match='sys exit called'):
                #No machine config
                parser = initParser(['-pc','plots_config.json','-bc','test_bc.json'])

            with pytest.raises(ValueError,match='sys exit called'):
                #Non-existent dir
                parser = initParser(['-pc','plots_config.json','-bc','test_bc.json','--dir','non_existent_dir'])


    def test_buildConfigList(self):
        """ Tests that for a given directory or benchmark config list, correct list is made
        Verifies the following cases:
        - Only benchmark config
        - Only dir
        - Dir + benchmark configs
        - using exclude
        """

        with tempfile.TemporaryDirectory() as tempdir:
            tempfiles = [tempfile.NamedTemporaryFile(dir=tempdir,suffix=".json") for _ in range(10)]

            parser = initParser(['-mc','machine_config.json','-bc'] + [tmp.name for tmp in tempfiles])
            assert set(parser.args.benchmark_config) == set([os.path.abspath(tmp.name) for tmp in tempfiles])

            parser = initParser(['-mc','machine_config.json','--dir', tempdir])
            assert set(parser.args.benchmark_config) == set([os.path.abspath(tmp.name) for tmp in tempfiles])

            parser = initParser(['-mc','machine_config.json','--dir', tempdir, '-bc', os.path.basename(tempfiles[0].name)])
            assert parser.args.benchmark_config == [os.path.abspath(tempfiles[0].name)]

            parser = initParser(['-mc','machine_config.json','--dir', tempdir,'--exclude', os.path.basename(tempfiles[0].name)])
            assert set(parser.args.benchmark_config) == set([os.path.abspath(tmp.name) for tmp in tempfiles[1:]])

            for tmp in tempfiles:
                tmp.close()


