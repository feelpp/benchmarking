from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode

class Repository:
    """ Base class for repositories.
    Designed for containing and manipulating a unique list of Components
    """
    def __init__(self,id:str) -> None:
        """
        Args:
            id (str): The id of the repository
        """
        self.data:list[GraphNode] = []
        self.id:str = id

    def __iter__(self) -> iter:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"< {self.id} : [{', '.join([str(d) for d in self.data])}] >"

    def add(self, item:GraphNode) -> None:
        """ Add an item to the repository, ensuring it is unique
        Args:
            item (object): The component to add
        """
        if item not in self.data and item.id not in [x.id for x in self.data]:
            self.data.append(item)

    def get(self, id:str) -> GraphNode:
        """ Get an item by its id
        Args:
            id (str): The id of the item to get
        """
        item = next(filter(lambda x: x.id == id, self.data), None)
        if item is None:
            raise KeyError(f"Item with id {id} not found in repository {self.id}")
        return item

    def has(self, id:str) -> bool:
        """ Return true if the component with id exists in data
        Args:
            id (str): The id of the component to check
        """
        return id in [x.id for x in self.data]

    def __getitem__(self,index:int) -> GraphNode:
        return self.data[index]

    def __len__(self):
        return len(self.data)