from feelpp.benchmarking.report.base.baseComponent import BaseComponent
import os

class Application(BaseComponent):
    """ Class representing an application module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of an application.
    """
    def __init__(self, id, display_name, description, main_variables):
        super().__init__(id, display_name, description)
        self.type = "application"
        self.main_variables = main_variables