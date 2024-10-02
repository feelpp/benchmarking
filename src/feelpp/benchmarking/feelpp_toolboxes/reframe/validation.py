import reframe.utility.sanity as sn

class ValidationHandler:
    def __init__(self, sanity_config):
        self.success = sanity_config.success
        self.errors = sanity_config.error

    def check_success(self,stdout):
        #TODO: FIX
        for suc in self.success:
            if sn.assert_not_found(suc,stdout):
                return False
        return True

    def check_errors(self,stdout):
        #TODO: FIX
        for err in self.errors:
            if sn.assert_found(err,stdout):
                return False
        return True