class Component:
    """ Base class for components """
    def __init__(self,id:str,parent_repository) -> None:
        """
        Args:
            id (str): The ID of the component.
            parent_repository (Repository) : Parent Repository
        """
        self.id = id
        self.parent_repository = parent_repository

    def __repr__(self) -> None:
        return f"<{self.id}>"
