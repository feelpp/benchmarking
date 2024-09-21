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

    def initModules(self, base_dir, renderer, parent_id, self_tag_id):
        """ Initialize the modules for the component.
        Creates the directory for the component and renders the index.adoc file
        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            parent_id (str): The catalog id of the parent component
            self_tag_id (str): The catalog id of the current component, to be used by their children as parent
        """
        module_path = os.path.join(base_dir, self.id)

        if not os.path.exists(module_path):
            os.mkdir(module_path)

        renderer.render(
            os.path.join(module_path, "index.adoc"),
            self.indexData(parent_id, self_tag_id)
        )

    def printHierarchy(self):
        """ Print the hierarchy of the component """
        print(f"{self.display_name}")
        for k, vs in self.tree.items():
            print(f"\t{k.display_name}")
            for v,reports in vs.items():
                print(f"\t\t{v.display_name} : {len(reports)}")