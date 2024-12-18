import reframe.utility.sanity as sn
import re

class ValidationHandler:
    """ Class to handle test validation and sanity functions"""
    def __init__(self, sanity_config):
        self.success = sanity_config.success
        self.errors = sanity_config.error

    def check_success(self,stdout):
        """ Checks that all given regex patterns are found in an output (can be sn.stdout) """
        return all(sn.assert_found(rf"{re.escape(pattern)}",stdout) for pattern in self.success)

    def check_errors(self,stdout):
        """ Checks that no given regex patterns are found in an output (can be sn.stdout) """
        return all(sn.assert_not_found(rf"{re.escape(pattern)}",stdout) for pattern in self.errors)