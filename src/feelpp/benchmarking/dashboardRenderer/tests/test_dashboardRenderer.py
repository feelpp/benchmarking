import pytest
from feelpp.benchmarking.dashboardRenderer.dashboardOrchestrator import DashboardOrchestrator
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema

class TestDashboardRenderer:

    components_config = {
        "views":{
            "a":{
                "d":{
                    "b":"c",
                    "c":"b"
                }
            },
            "d":{"a":{"b":"c"}},
            "b":{"c":{"a":"d"}}
        },
        "component_map":{
            "component_order":["a","b","c","d"],
            "mapping":{
                "a1":{
                    "b1": {
                        "c1":{ "d1":{"path":None} },
                        "c2":{ "d1":{"path":None} },
                    },
                    "b2":{
                        "c2":{ "d1":{"path":None} }
                    }
                },
                "a3":{
                    "b4":{
                        "c1":{ "d1":{"path":None} }
                    },
                    "b1":{
                        "c2":{ "d1":{"path":None} }
                    },
                }
            }
        },
        "components":{
            "a":{
                "a1": { "display_name":"A1 NodeComponent" },
                "a2": { "display_name":"A2 NodeComponent" },
                "a3": { "display_name":"A3 NodeComponent" }
            },
            "b":{
                "b1": { "display_name":"B1 NodeComponent" },
                "b2": { "display_name":"B2 NodeComponent" },
                "b3": { "display_name":"B3 NodeComponent" },
                "b4": { "display_name":"B4 NodeComponent" }
            },
            "c":{
                "c1": { "display_name":"C1 NodeComponent" },
                "c2": { "display_name":"C2 NodeComponent" }
            },
            "d":{
                "d1": { "display_name":"D1 NodeComponent" }
            }
        },
        "repositories":{
            "a":{ "display_name":"A" },
            "b":{ "display_name":"B" },
            "c":{ "display_name":"C" },
            "d":{ "display_name":"D" }
        }
    }


    def test_init(self):
        dashboard = DashboardOrchestrator(DashboardSchema(**self.components_config))

        for repo_id in ["a","b","c","d"]:
            assert all(self.components_config["views"].get(repo_id,{}).keys() == dashboard.getComponent(comp.id).views.keys() for comp in dashboard.getRepository(repo_id))


        # CHECK A1
        expected = { "d":{
            dashboard.getComponent("d1") : {
                "b": {
                    dashboard.getComponent("b1"): { "c":{ dashboard.getComponent("c1"): [], dashboard.getComponent("c2"): [] } },
                    dashboard.getComponent("b2"): { "c":{ dashboard.getComponent("c2"): [] } }
                },
                "c":{
                    dashboard.getComponent("c1"): { "b":{ dashboard.getComponent("b1"): [] } },
                    dashboard.getComponent("c2"): { "b":{ dashboard.getComponent("b1") : [], dashboard.getComponent("b2") : [] } }
                }
            }
        }}
        assert expected == dashboard.getComponent("a1").views

        # CHECK A2
        assert dashboard.getComponent("a2").views == {"d" : {}}

        #CHECK A3
        expected = { "d":{
            dashboard.getComponent("d1") : {
                "b": {
                    dashboard.getComponent("b1"): { "c":{ dashboard.getComponent("c2"): [] } },
                    dashboard.getComponent("b4"): { "c":{ dashboard.getComponent("c1"): [] } }
                },
                "c":{
                    dashboard.getComponent("c1"): { "b":{ dashboard.getComponent("b4"): [] } },
                    dashboard.getComponent("c2"): { "b":{ dashboard.getComponent("b1") : [] } }
                }
            }
        }}
        assert dashboard.getComponent("a3").views == expected

        #CHECK B1

        expected = { "c":{
            dashboard.getComponent("c1"): {
                "a": { dashboard.getComponent("a1") : { "d" : { dashboard.getComponent("d1") : []} } }
            },
            dashboard.getComponent("c2"): {
                "a": {
                    dashboard.getComponent("a1") :{"d": {dashboard.getComponent("d1") : []}},
                    dashboard.getComponent("a3"): {"d": {dashboard.getComponent("d1") : []}}
                }
            }
        }}

        assert dashboard.getComponent("b1").views == expected

        #CHECK B2  {"c":{"a":"d"}}
        expected = { "c":{
            dashboard.getComponent("c2"): {
                "a": { dashboard.getComponent("a1") :{"d": {dashboard.getComponent("d1") : []}} }
            }
        }}
        assert dashboard.getComponent("b2").views == expected

        #CHECK B3
        assert dashboard.getComponent("b3").views == {"c": {}}

        #CHECK B4
        expected = { "c":{
            dashboard.getComponent("c1"): {
                "a": { dashboard.getComponent("a3") :{"d": {dashboard.getComponent("d1") : []}} }
            }
        }}
        assert dashboard.getComponent("b4").views == expected

        #CHECK C (empty)
        assert all(comp.views == {} for comp in dashboard.getRepository("c"))

        #CHECK D1
        expected = { "a" : {
            dashboard.getComponent("a1") : {
                "b" : {
                    dashboard.getComponent("b1") : { "c" : {dashboard.getComponent("c1") : [], dashboard.getComponent("c2") : []}},
                    dashboard.getComponent("b2") : { "c" : {dashboard.getComponent("c2") : []} }
                }
            },
            dashboard.getComponent("a3") : {
                "b": {
                    dashboard.getComponent("b4") : { "c" : {dashboard.getComponent("c1") : []} },
                    dashboard.getComponent("b1") : { "c" : {dashboard.getComponent("c2") : []} }
                }
            }
        }}

        assert dashboard.getComponent("d1").views == expected
