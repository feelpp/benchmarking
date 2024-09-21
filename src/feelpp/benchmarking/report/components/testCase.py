import os
from feelpp.benchmarking.report.components.baseComponent import BaseComponent

class TestCase(BaseComponent):
    def __init__(self, id, display_name, description, application):
        super().__init__(id, display_name, description)

        self.tree[application] = {}