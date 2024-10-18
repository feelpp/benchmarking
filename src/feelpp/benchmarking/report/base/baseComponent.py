import os,copy
from feelpp.benchmarking.report.base.model import AggregationModel

class BaseComponent:
    """ Base class for all components (machine, application, test case) """
    def __init__(self, id, display_name, description):
        """
        tree: dict[BaseComponent, dict[BaseComponent, list[AtomicReport]]]
        Args:
            id (str): The id of the component
            display_name (str): The display name of the component
            description (str): The description of the component
        """
        self.id = id
        self.display_name = display_name
        self.description = description

        self.tree = {}
        self.model_tree = {}
        self.main_variables = []

    def indexData(self,parent_id, self_tag_id):
        """ Get the data for the index.adoc file
        Args:
            parent_id (str): The catalog id of the parent component
            self_tag_id (str): The catalog id of the current component, to be used by their children as parent
        Returns:
            dict: The data for the index.adoc file
        """
        return dict(
            title = self.display_name,
            layout = "toolboxes",
            tags = f"catalog, toolbox, {self_tag_id}",
            description = self.description,
            parent_catalogs = parent_id,
            illustration = f"ROOT:{self.id}.jpg"
        )

    def initModule(self, base_dir, renderer, parent_id, self_tag_id):
        """ Initialize the modules for the component.
        Creates the directories for the component and renders the index.adoc file
        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            parent_id (str): The catalog id of the parent component
            self_tag_id (str): The catalog id of the current component, to be used by their children as parent
        """
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        module_path = os.path.join(base_dir, self.id)

        if not os.path.exists(module_path):
            os.mkdir(module_path)

        renderer.render(
            os.path.join(module_path, "index.adoc"),
            self.indexData(parent_id, self_tag_id)
        )

    def initModules(self, base_dir, renderer, parent_id):
        """ Initialize the modules for the component.
        Creates the directories recursively for the component and its children and renders the index.adoc files for each.

        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            parent_id (str,optional): The catalog id of the parent component.
        """
        self.initModule( base_dir, renderer, parent_id, self.id)
        for child, grandchildren in self.tree.items():
            child.initModule(os.path.join(base_dir,self.id), renderer, parent_id = self.id, self_tag_id = f"{self.id}-{child.id}")
            for grandchild in grandchildren:
                grandchild.initModule(os.path.join(base_dir,self.id,child.id), renderer, parent_id = f"{self.id}-{child.id}", self_tag_id = f"{self.id}-{child.id}-{grandchild.id}")

    def printHierarchy(self):
        """ Print the hierarchy of the component """
        print(f"{self.display_name}")
        for k, vs in self.tree.items():
            print(f"\t{k.display_name}")
            for v,reports in vs.items():
                print(f"\t\t{v.display_name} : {len(reports)}")

    def initOverviewModels(self,overview_config):
        if not self.tree:
            return

        self_config = overview_config[self.type]["overview"]
        for i in range(len(self_config)):
            self_config[i]["variables"] = self.main_variables

        self.model_tree = {
            "overview": None,
            "plots_config":copy.deepcopy(self_config),
            "children":{}
        }

        for child, grandchildren in self.tree.items():
            child_config = overview_config[self.type][child.type]["overview"]
            for i in range(len(child_config)):
                child_config[i]["variables"] = self.main_variables + child.main_variables
            self.model_tree["children"][child] = {
                "overview":None,
                "plots_config":copy.deepcopy(child_config),
                "children":{}
            }
            for grandchild, reports in grandchildren.items():
                grandchild_config = overview_config[self.type][child.type][grandchild.type]["overview"]
                for i in range(len(grandchild_config)):
                    grandchild_config[i]["variables"] = self.main_variables + child.main_variables + grandchild.main_variables

                self.model_tree["children"][child]["children"][grandchild] = {
                    "overview" : AggregationModel({ report.date: report.model.master_df for report in reports }, index_label="date"),
                    "plots_config":copy.deepcopy( grandchild_config)
                }
            self.model_tree["children"][child]["overview"] = AggregationModel( { gc.id : model["overview"].master_df for gc, model in self.model_tree["children"][child]["children"].items() }, index_label=grandchild.type )

        self.model_tree["overview"] = AggregationModel({ch.id : v["overview"].master_df for ch, v in self.model_tree["children"].items() },index_label=child.type)

    def createOverview(self,base_dir,renderer,parents,plots_config,master_df):
        renderer.render(
            os.path.join(base_dir,*[parent.id for parent in parents],"overview.adoc"),
            data = dict(
                parent_catalogs = "-".join([parent.id for parent in parents]),
                plots_config = plots_config,
                master_df = master_df,
                parents = parents
            )
        )


    def createOverviews(self,base_dir,renderer):
        if self.model_tree == {}:
            return

        self.createOverview(
            base_dir,renderer, parents=[self],
            plots_config=self.model_tree["plots_config"],
            master_df=self.model_tree["overview"].master_df.to_dict()
        )

        for child, child_dict, in self.model_tree["children"].items():
            self.createOverview(
                base_dir,renderer, parents=[self,child],
                plots_config=child_dict["plots_config"],
                master_df=child_dict["overview"].master_df.to_dict()
            )

            for grandchild, atomic_dict in child_dict["children"].items():
                self.createOverview(
                    base_dir,renderer, parents=[self,child,grandchild],
                    plots_config=atomic_dict["plots_config"],
                    master_df=atomic_dict["overview"].master_df.to_dict()
                )