import json, os

class WebsiteConfig:
    def __init__(self,basepath):
        self.config_filepath = os.path.join(basepath,"website_config.json")

        if os.path.exists(self.config_filepath):
            with open(self.config_filepath,"r") as cfg:
                self.config = json.load(cfg)
        else:
            self.config = {
                "execution_mapping":{},
                "machines":{},
                "use_cases":{},
                "applications":{}
            }

    def updateExecutionMapping(self,application,machine,use_case, report_itempath):
        if application not in self.config["execution_mapping"]:
            self.config["execution_mapping"][application] = {}

        if machine not in self.config["execution_mapping"][application]:
            self.config["execution_mapping"][application][machine] = {}

        self.config["execution_mapping"][application][machine][use_case] = report_itempath

    def updateMachine(self,machine):
        if machine not in self.config["machines"]:
            self.config["machines"][machine] = {
                "display_name":machine,
                "description":""
            }

    def updateUseCase(self,use_case):
        if use_case not in self.config["use_cases"]:
            self.config["use_cases"][use_case] = {
                "display_name":use_case,
                "description":""
            }

    def updateApplication(self,application):
        if application not in self.config["applications"]:
            self.config["applications"][application] = {
                "display_name":application,
                "description":"",
                "main_variables":[]
            }

    def save(self):
        with open(self.config_filepath,"w") as cfg:
            cfg.write(json.dumps(self.config))
