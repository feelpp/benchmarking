""" Tests for commandBuilder module"""


import pytest, re, os
from feelpp.benchmarking.reframe.commandBuilder import CommandBuilder
from unittest.mock import patch

class MockMachineConfig:
    def __init__(self,
        machine="test_machine",
        reports_base_dir="./mock/report_dir",
        reframe_base_dir="./mock/reframe_dir",
        execution_policy="mock_exec_policy"
    ):
        self.machine = machine
        self.reports_base_dir = reports_base_dir
        self.reframe_base_dir = reframe_base_dir
        self.execution_policy = execution_policy

class MockParser:
    class MockArgs:
        def __init__(self,dry_run,verbose):
            self.dry_run = dry_run
            self.verbose = verbose
            self.custom_rfm_config = None
            self.reframe_args = ""

    def __init__(self,dry_run= False,verbose=1):
        self.args = self.MockArgs(dry_run= dry_run,verbose=verbose)




@pytest.mark.parametrize(("machine_config","parser"),[
    # Default configuration
    (MockMachineConfig(), MockParser()),

    # Test with different machine configurations
    (MockMachineConfig(machine="machine_A", reports_base_dir="./mock/reports_A", reframe_base_dir="./mock/reframe_A", execution_policy="policy_A"), MockParser()),
    (MockMachineConfig(machine="machine_B", reports_base_dir="./mock/reports_B", reframe_base_dir="./mock/reframe_B", execution_policy="policy_B"), MockParser()),

    # Test with dry_run flag set to True
    (MockMachineConfig(), MockParser(dry_run=True, verbose=1)),
    (MockMachineConfig(machine="machine_C", reports_base_dir="./mock/reports_C", reframe_base_dir="./mock/reframe_C", execution_policy="policy_C"), MockParser(dry_run=True, verbose=2)),

    # Test with different verbosity levels
    (MockMachineConfig(), MockParser(dry_run=False, verbose=0)),
    (MockMachineConfig(), MockParser(dry_run=False, verbose=2)),

    # Test with additional or alternative machine configurations
    (MockMachineConfig(machine="machine_X", reports_base_dir="./mock/reports_X", reframe_base_dir="./mock/reframe_X", execution_policy="policy_X"), MockParser(dry_run=False, verbose=1)),
    (MockMachineConfig(machine="machine_Y", reports_base_dir="./mock/reports_Y", reframe_base_dir="./mock/reframe_Y", execution_policy="policy_Y"), MockParser(dry_run=False, verbose=3)),

    # Test with mixed configurations
    (MockMachineConfig(machine="machine_1", reports_base_dir="./mock/reports_1", reframe_base_dir="./mock/reframe_1", execution_policy="policy_1"), MockParser(dry_run=True, verbose=1)),
    (MockMachineConfig(machine="machine_2", reports_base_dir="./mock/reports_2", reframe_base_dir="./mock/reframe_2", execution_policy="policy_2"), MockParser(dry_run=False, verbose=0)),
])
class TestCommandBuilder:
    """Tests for the CommandBuilder class"""

    @pytest.fixture(scope="function")
    def cmd_builder(self, machine_config, parser):
        return CommandBuilder(machine_config, parser)

    def test_init(self,cmd_builder,machine_config,parser):
        """Tests the correct initialization of the CommandBuilder class"""
        assert cmd_builder.machine_config == machine_config
        assert cmd_builder.parser == parser
        assert re.match(r"^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}$", cmd_builder.current_date)

    def test_getScriptRootDir(self,cmd_builder):
        """Tests the getScriptRootDir method of CommandBuilder"""
        script_root_dir = cmd_builder.getScriptRootDir()
        assert os.path.isabs(script_root_dir)

    def test_buildConfigFilePath(self,cmd_builder,machine_config):
        """Tests the buildConfigFilePath method of the CommandBuilder"""
        cfg_filepath = cmd_builder.buildConfigFilePath()
        assert cfg_filepath.endswith(".py")
        assert os.path.basename(cfg_filepath) == f"reframe.py"
        assert os.path.dirname(cfg_filepath).split("/")[-1] == machine_config.machine


    def test_createReportFolder(self,cmd_builder,machine_config):
        """ Tests the createReportFolder method of the CommandBuilder"""
        executable ="test_executable"
        use_case ="test_use_case"
        expected_path = f"{machine_config.reports_base_dir}/{executable}/{use_case}/{machine_config.machine}/"+cmd_builder.current_date

        with patch("os.path.exists", return_value=False):
            with patch("os.makedirs") as mock_makedirs:
                result = cmd_builder.createReportFolder(executable, use_case)
                print(result)
                print(expected_path)

                assert os.path.normpath(result) == os.path.normpath(expected_path)
                mock_makedirs.assert_called_once_with(expected_path)

        with patch("os.path.exists", return_value=True):
            with patch("os.makedirs") as mock_makedirs:
                result = cmd_builder.createReportFolder(executable, use_case)
                mock_makedirs.assert_not_called()

                assert os.path.normpath(result) == os.path.normpath(expected_path)

    def test_buildExecutionMode(self,cmd_builder,parser):
        """Tests the buildExecutionMode method of the CommandBuilder"""
        if parser.args.dry_run:
            assert "--dry-run" in cmd_builder.buildExecutionMode().split(" ")
            assert "-r" not in cmd_builder.buildExecutionMode().split(" ")
        else:
            assert "--dry-run" not in cmd_builder.buildExecutionMode().split(" ")
            assert "-r" in cmd_builder.buildExecutionMode().split(" ")

    def test_buildCommand(self,cmd_builder,machine_config,parser):
        """Tests the buildCommand method of the CommandBuilder"""
        timeout = "0-00:01:00"
        executable ="test_executable"
        use_case ="test_use_case"

        report_folder_path = os.path.join(machine_config.reports_base_dir,executable,use_case,machine_config.machine,str(cmd_builder.current_date))
        cmd_builder.report_folder_path = report_folder_path

        expected_command = (
            "reframe "
            f"-C {cmd_builder.getScriptRootDir()}/config/machineConfigs/{machine_config.machine}/reframe.py "
            f"-c {cmd_builder.getScriptRootDir()}/regression.py "
            f"-S report_dir_path={machine_config.reports_base_dir}/{executable}/{use_case}/{machine_config.machine}/{cmd_builder.current_date} "
            f"--system={machine_config.machine} "
            f"--exec-policy={machine_config.execution_policy} "
            f"--prefix={machine_config.reframe_base_dir} "
            f"--report-file={str(os.path.join(report_folder_path,'reframe_report.json'))} "
            f"-J time={timeout} "
            f"--perflogdir={os.path.join(machine_config.reframe_base_dir,'logs')} "
        )
        expected_command += "--dry-run --exec-policy serial" if parser.args.dry_run else "-r"

        assert expected_command == cmd_builder.buildCommand(timeout)