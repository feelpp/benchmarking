import os

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


    def createOverview(self, base_dir, renderer, data):
        """ Create an overview page for the component
        Args:
            base_dir (str): The base directory for the module
            renderer (Renderer): The renderer to use
            data (dict): The data to be passed to the template
        """
        output_folder_path = os.path.join(base_dir, self.id)

        if not os.path.exists(output_folder_path):
            raise FileNotFoundError(f"The folder {output_folder_path} does not exist. Modules should be initialized beforehand ")

        renderer.render(f"{output_folder_path}/overview.adoc", data )


    def createOverviews(self, base_dir, renderer):
        """ Create the overview for an app-machine-usecase combination, from aggregating atomic report data
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """
        for child, grandchildren in self.tree.items():
            for grandchild, atomic_reports in grandchildren.items():
                grandchild.createOverview(
                    os.path.join(base_dir,self.id,child.id), renderer,
                    data = dict(
                        reports_dfs = { report.date: report.model.master_df.to_dict(orient='dict') for report in atomic_reports },
                        parent_catalogs = f"{self.id}-{child.id}-{grandchild.id}",
                    )
                )


    def printHierarchy(self):
        """ Print the hierarchy of the component """
        print(f"{self.display_name}")
        for k, vs in self.tree.items():
            print(f"\t{k.display_name}")
            for v,reports in vs.items():
                print(f"\t\t{v.display_name} : {len(reports)}")