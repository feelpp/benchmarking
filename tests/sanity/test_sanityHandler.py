import pytest
from feelpp.benchmarking.reframe.validation import ValidationHandler
from unittest.mock import patch
import reframe.utility.sanity as sn
from reframe.core.exceptions import SanityError

class MockSanityConfig:
    """Mock pydantic schema class for sanity configuration"""
    def __init__(self, success=None, error=None):
        self.success = success or []
        self.error = error or []


@pytest.fixture
def sample_stdout():
    """ Fixture for a sample stoud"""
    return """
        This is a test containing pattern1 and [pattern1] and \\[pattern1\\].
        It matches the pattern 'pattern.*' and includes a number 123.
        It should not contain errorpattern or [errorpattern] or \\[errorpattern\\].
        There are no 3-digit errors in this output.
    """

def generatSuccessPatternTestCases():
    #TODO: Add more cases
    """Generates various test cases for success patterns."""
    return [
        ("pattern1", True),
        ("[pattern1]", True),
        ("\\[pattern1\\]", True),
        ("pattern.*", True),
        ("nonexistentpattern", False),
    ]

def generateErrorPatternTestCases():
    #TODO: Add more cases
    """Generates various test cases for success patterns."""
    return [
        ("errorpattern", False),
        ("[errorpattern]", False),
        ("\\[errorpattern\\]", False),
        ("noerrorpattern", True),
    ]



class TestValidationHandler:
    #TODO: NOT ALL REGEX PATTERNS ARE SUPPORTED DUE TO ESCAPED CHARS,
    # THIS SHOULD BE DESCRIBED IN AN ISSUE AND ADD RESPECTIVE UNIT TESTS WHEN IMPLEMENTED

    @pytest.mark.parametrize("pattern, expected_result", generatSuccessPatternTestCases())
    def test_checkSuccess(self,pattern,expected_result,sample_stdout,monkeypatch):
        validation_handler = ValidationHandler(MockSanityConfig(success=[pattern],error=[]))

        monkeypatch.setattr(sn, 'assert_found', sn.assert_found_s)

        if expected_result:
            result = validation_handler.check_success(sample_stdout)
            assert result == expected_result
        else:
            with pytest.raises(SanityError):
                validation_handler.check_success(sample_stdout)

    @pytest.mark.parametrize("pattern, expected_result", generateErrorPatternTestCases())
    def test_checkErrors(self,pattern,expected_result,sample_stdout,monkeypatch):
        validation_handler = ValidationHandler(MockSanityConfig(success=[],error=[pattern]))

        monkeypatch.setattr(sn, 'assert_not_found', sn.assert_not_found_s)

        if expected_result:
            result = validation_handler.check_errors(sample_stdout)
            assert result == expected_result
        else:
            with pytest.raises(SanityError):
                validation_handler.check_errors(sample_stdout)


