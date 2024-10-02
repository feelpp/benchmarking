import reframe.utility.sanity as sn

class ValidationHandler:
    def __init__(self, sanity_config):
        self.success = sanity_config.success
        self.errors = sanity_config.error

    def check_success(self,stdout):
        return all(sn.assert_found(pattern,stdout) for pattern in self.success)

    def check_errors(self,stdout):
        return all(sn.assert_not_found(pattern,stdout) for pattern in self.errors)