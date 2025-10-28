import json, os

class WebsiteConfigCreator:
    def __init__(self,basepath):
        self.config_filepath = os.path.join(basepath,"website_config.json")

        if os.path.exists(self.config_filepath):
            with open(self.config_filepath,"r") as cfg:
                self.config = json.load(cfg)
        else:
            self.config = dict(
                dashboard_metadata = {"title":"feelpp.benchmarking"},
                views = {
                    "machines": { "applications": "use_cases", "use_cases": "applications" },
                    "applications": { "use_cases": "machines" },
                    "use_cases": { "applications": "machines" }
                },
                repositories={
                    "machines": { "title": "Supercomputers", "description": "Systems" },
                    "applications": { "title": "Applications", "description": "Applications" },
                    "use_cases": { "title": "Use Cases", "description": "Use Cases" }
                },
                components={
                    "machines":{},
                    "use_cases":{},
                    "applications":{}
                },
                component_map=dict(
                    component_order = ["machines","applications","use_cases"],
                    mapping = {}
                )
            )

    def updateExecutionMapping(self,application, machine,use_case, report_itempath):
        if machine not in self.config["component_map"]["mapping"]:
            self.config["component_map"]["mapping"][machine] = {}

        if application not in self.config["component_map"]["mapping"][machine]:
            self.config["component_map"]["mapping"][machine][application] = {}

        self.config["component_map"]["mapping"][machine][application][use_case] = {
            "path":report_itempath,
            "platform":"local",
            "template_info":{ #TODO: WARNING THIS WILL BREAK IF EXECUTED ELSEWHERE...
                "template":"./src/feelpp/benchmarking/report/templates/reframeReport.adoc.j2",
                "data":[
                    { "filepath": "reframe_report.json", "prefix": "rfm" },
                    { "filepath":"plots.json", "prefix":"plots" },
                    { "filepath":"partials/", "action":"copy", "prefix":"descriptions" },
                    { "use_case":use_case, "application":application, "machine": machine }
                ]
            }
        }

    def updateMachine(self,machine):
        if machine not in self.config["components"]["machines"]:
            self.config["components"]["machines"][machine] = {
                "title":machine, "description":""
            }

    def updateUseCase(self,use_case):
        if use_case not in self.config["components"]["use_cases"]:
            self.config["components"]["use_cases"][use_case] = {
                "title":use_case, "description":""
            }

    def updateApplication(self,application):
        if application not in self.config["components"]["applications"]:
            self.config["components"]["applications"][application] = {
                "title":application, "description":""
            }

    def save(self):
        with open(self.config_filepath,"w") as cfg:
            cfg.write(json.dumps(self.config))
