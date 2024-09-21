import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent

class TestCase(BaseComponent):
    """ Class representing a test case module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of a test case.
    """
    def __init__(self, id, display_name, description, application):
        """ Constructor for the TestCase class
        tree attribute should contain only ONE application

        Args:
            id (str): The id of the test case
            display_name (str): The display name of the test case
            description (str): The description of the test case
            application (Application): The application to which the test case
        """
        super().__init__(id, display_name, description)

        self.tree[application] = {}