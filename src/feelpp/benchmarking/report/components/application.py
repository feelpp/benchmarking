from feelpp.benchmarking.report.components.baseComponent import BaseComponent
import os

class Application(BaseComponent):
    def __init__(self, id, display_name, description):
        super().__init__(id, display_name, description)