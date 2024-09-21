from feelpp.benchmarking.report.components.baseComponent import BaseComponent

class Application(BaseComponent):
    """ Class representing an application module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of an application.
    """
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)