import os

class Repository:
    """ Base class for repositories.
    Designed for containing and manipulating a unique list of items
    """
    def __init__(self):
        self.data = []

    def __iter__(self):
        """ Iterator for the repository """
        return iter(self.data)

    def add(self, item):
        """ Add an item to the repository, ensuring it is unique
        Args:
            item (object): The item to add
        """
        if item not in self.data:
            self.data.append(item)

    def get(self, id):
        """ Get an item by its id """
        return next(filter(lambda x: x.id == id, self.data))

    def link(self, other_components, execution_mapping):
        """ Pure virtual function to link the items of the repository to other components.
         It will update the tree attribute of the items """
        pass

class ModuleRepository(Repository):
    """Base class representing a collection of components that define a module (machine, application, useCase) """

    def printHierarchy(self):
        """ Print the hierarchy of the repository """
        for item in self.data:
            item.printHierarchy()

    def indexData(self, parent_id, self_tag_id ):
        """ Get the data for the index.adoc file for the repository
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

    def initModule(self, base_dir, renderer, self_tag_id, parent_id = "catalog-index"):
        """ Initialize the module for repository.
        Creates the directory for the repository and renders the index.adoc file
        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            self_tag_id (str): The catalog id of the current reposirory, to be used by their children as parent
            parent_id (str): The catalog id of the parent component
        """
        module_path = os.path.join(base_dir, self.id)

        if not os.path.exists(module_path):
            os.mkdir(module_path)

        renderer.render(
            os.path.join(module_path,"index.adoc"),
            self.indexData(parent_id,self_tag_id)
        )

    def initModules(self, base_dir, renderer, parent_id = "catalog-index"):
        """ Inits the repository module and calls the initModules method of each item in the repository.
        Args:
            base_dir (str): The base directory for the modules
            renderer (Renderer): The renderer to use
            parent_id (str,optional): The catalog id of the parent component. Defaults to "supercomputers".
        """
        self.initModule(base_dir,renderer,self_tag_id=self.id, parent_id=parent_id)
        for item in self.data:
            item.initModules(os.path.join(base_dir,self.id), renderer, self.id)

    def createOverviews(self, base_dir, renderer):
        for item in self.data:
            item.createOverviews(os.path.join(base_dir,self.id),renderer)