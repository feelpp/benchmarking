from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
from typing import List, Iterator, Optional

class Repository:
    """ Base class for repositories.
    Designed for containing and manipulating a UNIQUE list of **GraphNode** components.
    It provides basic methods for adding, retrieving, and checking for the existence
    of components, and supports iteration and indexing.
    """
    def __init__( self, id:str ) -> None:
        """
        Args:
            id (str): The unique identifier of the repository.
        """
        self.data : List[GraphNode] = []
        self.id : str = id

    def __iter__( self ) -> Iterator[GraphNode]:
        return iter( self.data )

    def __repr__( self ) -> str:
        return f"< {self.id} : [{', '.join([str(d) for d in self.data])}] >"

    def __getitem__( self, index:int ) -> GraphNode:
        return self.data[index]

    def __len__( self ) -> int:
        return len(self.data)

    def add( self, item:GraphNode ) -> None:
        """
        Adds a **GraphNode** component to the repository, ensuring its uniqueness
        based on both object identity and the component's ID.

        Args:
            item (GraphNode): The component to add.
        """
        if item not in self.data and item.id not in [x.id for x in self.data]:
            self.data.append( item )

    def get( self, id:str ) -> GraphNode:
        """
        Retrieves a component from the repository by its ID.

        Args:
            id (str): The ID of the component to retrieve.
        Returns:
            GraphNode: The component with the matching ID.
        Raises:
            KeyError: If no item with the given ID is found in the repository.
        """
        item = next( filter(lambda x: x.id == id, self.data), None )
        if item is None:
            raise KeyError(f"Item with id {id} not found in repository {self.id}")
        return item

    def has( self, id:str ) -> bool:
        """
        Checks if a component with the specified ID exists in the repository.

        Args:
            id (str): The ID of the component to check.
        Returns:
            bool: True if the component exists, False otherwise.
        """
        return id in [x.id for x in self.data]
