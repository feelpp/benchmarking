from feelpp.benchmarking.jsonWithComments import JSONWithCommentsDecoder
import json, os

class WebsiteConfigCreator:
    def __init__(self,basepath):
        self.config_filepath = os.path.join(basepath,"website_config.json")

        if os.path.exists(self.config_filepath):
            with open(self.config_filepath,"r") as cfg:
                self.config = json.load(cfg, cls=JSONWithCommentsDecoder)
        else:
            self.config = dict(
                dashboard_metadata = {
                    "template": "${TEMPLATE_DIR}/dashboardOverview.adoc.j2",
                    "data":{"title":"feelpp.benchmarking"}
                },
                template_defaults = {
                    "leaves":{
                        "template":"${TEMPLATE_DIR}/reframeReport.adoc.j2",
                        "data":[
                            { "filepath":"report.json", "prefix":"report", "action":"json2adoc"},
                            { "filepath":"partials/", "action":"copy", "prefix":"descriptions" },
                            { "filepath":"logs/", "action":"copy", "prefix":"logs" }
                        ]
                    },
                    "components":{
                        "all":{
                            "template": "${TEMPLATE_DIR}/overview.adoc.j2",
                        },
                        "machines":{
                            "template": "${TEMPLATE_DIR}/machineOverview.adoc.j2",
                            "data":{"card_type":"machine", "card_image":"fa-solid fa-microchip"}
                        },
                        "applications":{"card_type":"application", "card_image":"fa-solid fa-diagram-project"},
                        "use_cases":{"card_type":"usecase", "card_image":"fa-solid fa-briefcase"}
                    },
                    "repositories":{
                        "template": "${TEMPLATE_DIR}/overview.adoc.j2"
                    },
                },
                views = {
                    "machines": { "applications": "use_cases" },
                    "applications": { "use_cases": "machines" }
                },
                repositories={
                    "machines": { "title": "Supercomputers", "description": "Systems","card_type":"machine" },
                    "applications": { "title": "Applications", "description": "Applications","card_type":"application" },
                    "use_cases": { "title": "Use Cases", "description": "Use Cases","card_type":"usecase" }
                },
                components={
                    "machines":{},
                    "use_cases":{},
                    "applications":{}
                },
                component_map=dict()
            )

    def updateExecutionMapping(self,application, machine,use_case, report_itempath):
        if machine not in self.config["component_map"]:
            self.config["component_map"][machine] = {}

        if application not in self.config["component_map"][machine]:
            self.config["component_map"][machine][application] = {}

        self.config["component_map"][machine][application][use_case] = {
            "path":report_itempath,
            "platform":"local",
            "template_info":{ "use_case":use_case, "application":application, "machine": machine }
        }

    def updateMachine(self,machine):
        if machine not in self.config["components"]["machines"]:
            self.config["components"]["machines"][machine] = {
                "title":machine.title(), "description":""
            }

    def updateUseCase(self,use_case):
        if use_case not in self.config["components"]["use_cases"]:
            self.config["components"]["use_cases"][use_case] = {
                "title":use_case.title(), "description":""
            }

    def updateApplication(self,application):
        if application not in self.config["components"]["applications"]:
            self.config["components"]["applications"][application] = {
                "title":application.title(), "description":""
            }

    def save(self):
        with open(self.config_filepath,"w") as cfg:
            cfg.write(json.dumps(self.config))
