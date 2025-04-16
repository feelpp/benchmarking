from feelpp.benchmarking.dashboardRenderer.repository.node import NodeComponentRepository
from feelpp.benchmarking.dashboardRenderer.repository.leaf import LeafComponentRepository
from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.component.base import Component

class RepositoryRegistry:
    """ Registry for storing and dispatching component repositories. """
    def __init__(self) -> None:
        self.node_repositories: list[NodeComponentRepository] = []
        self.leaf_repository: LeafComponentRepository = None


    def __getitem__(self,i):
        if i < len(self.node_repositories):
            return self.node_repositories[i]
        elif i == len(self.node_repositories):
            return self.leaf_repository
        else:
            raise IndexError

    def addNodeRepository(self, node_repository: NodeComponentRepository) -> None:
        """ Add a node repository to the registry.
        Args:
            node_repository (NodeComponentRepository): The node repository to add.
        """
        self.node_repositories.append(node_repository)

    def setLeafRepository(self, leaf_repository: LeafComponentRepository) -> None:
        """ Set the leaf repository for the registry.
        Args:
            leaf_repository (LeafComponentRepository): The leaf repository to set.
        """
        self.leaf_repository = leaf_repository

    def getComponent(self,id:str) -> Component:
        """ Get a component by its ID.
        Args:
            id (str): The ID of the component to retrieve.
        Returns:
            Component: The component with the specified ID, or None if not found.
        """
        for repo in self.node_repositories:
            if repo.has(id):
                return repo.get(id)
        if self.leaf_repository and self.leaf_repository.has(id):
            return self.leaf_repository.get(id)

        raise ValueError(f"Component {id} not found")

    def getRepositoryByComponentId(self, id:str) -> Repository:
        """ Get the repository containing a component by its ID.
        Args:
            id (str): The ID of the component to retrieve the repository for.
        Returns:
            Repository: The repository containing the component with the specified ID, or None if not found.
        """
        for repo in self.node_repositories:
            if repo.has(id):
                return repo
        if self.leaf_repository and self.leaf_repository.has(id):
            return self.leaf_repository

    def getRepository(self,id:str)-> Repository:
        """ Get a repository by its ID.
        Args:
            id (str): The ID of the repository to retrieve.
        Returns:
            Repository: The repository with the specified ID, or None if not found.
        """
        for repo in self.node_repositories:
            if repo.id == id:
                return repo
        if self.leaf_repository and self.leaf_repository.id == id:
            return self.leaf_repository

        raise ValueError(f"Repository {id} not found")

    def __repr__(self) -> str:
        s = ""
        for node_repo in self.node_repositories:
            s += f"{node_repo}\n"
        if self.leaf_repository is not None:
            s += f"{self.leaf_repository}"
        return s

    def printViews(self) -> None:
        """ Print the views of all repositories in the registry. """
        for node_repo in self.node_repositories:
            print( node_repo.id )
            node_repo.printViews()