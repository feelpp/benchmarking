from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.component.leaf import LeafComponent
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import LeafMetadata
from feelpp.benchmarking.dashboardRenderer.views.leaf import LeafComponentView
import os

class LeafLoader:
    """ Abstract class for loading leaf components. """
    def __init__(self, location:str,template_info) -> None:
        """
        Args:
            location (str): The location of the leaf components.
        """
        self.location = location
        self.template_info = template_info

    def load(self,repository:Repository,parent_ids:list[str]) -> None:
        """
        Load leaf components into the repository.
        Args:
            repository (Repository): The repository to load components into.
            parent_ids (list[str]): List of parent IDs for the components.
        """
        raise NotImplementedError("Pure virtual method, must be implemented in derived classes.")


class LocalLeafLoader(LeafLoader):
    """ Loader for local leaf components. """
    def __init__(self, location:str, template_info) -> None:
        """
        Args:
            location (str): The local directory containing leaf components.
        Raises:
            FileNotFoundError: If the specified location does not exist.
        """
        super().__init__(location,template_info)

        if not os.path.exists(location):
            raise FileNotFoundError(f"{location} does not contain any files")

    def load(self,repository:Repository, parent_ids:list[str]) -> None:
        """
        Load local leaf components (in the filesystem) into the repository.
        Args:
            repository (Repository): The repository to load components into.
            parent_ids (list[str]): List of parent IDs for the components.
        """
        for leaf_component_dir in os.listdir(self.location):
            repository.add(LeafComponent(
                leaf_component_dir,repository,parent_ids,
                LeafComponentView(
                    leaf_component_dir,
                    self.template_info,
                    os.path.join(self.location,leaf_component_dir)
                )
            ))


class LeafLoaderFactory:
    """ Factory class for creating leaf loaders. """
    @staticmethod
    def create(leaf_config: LeafMetadata) -> LeafLoader:
        """
        Create a leaf loader based on the configuration.
        Args:
            leaf_config (LeafMetadata): The configuration for the leaf component.
        Returns:
            LeafLoader: An instance of a leaf loader.
        Raises:
            ValueError: If the path is not defined in the configuration.
            NotImplementedError: If the platform is not supported.
        """
        if leaf_config.path is None:
            raise ValueError("Leaf path is not defined")

        if leaf_config.platform == "local":
            return LocalLeafLoader(leaf_config.path,leaf_config.template_info)
        else:
            raise NotImplementedError("Remote locations not yet implemented")

