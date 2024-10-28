from feelpp.benchmarking.report.base.baseComponent import BaseComponent
import os

class Machine(BaseComponent):
    """ Class representing a machine module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of a machine.
    """
    def __init__(self, id, display_name, description):
        """ Constructor for the Machine class
        Args:
            id (str): The id of the machine
            display_name (str): The display name of the machine
            description (str): The description of the machine
        """
        super().__init__(id, display_name, description)
        self.type = "machine"