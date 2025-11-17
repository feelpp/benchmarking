""" Tests related to template rendering """

from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
import pytest
import tempfile


class TestRenderer:

    renderer = TemplateRenderer("./tests/data/templates/","template_test.adoc.j2")

    def test_render(self):
        """ Tests that the renderer correctly renders the template with given data"""
        with tempfile.NamedTemporaryFile(dir = "./tests/data") as tmp:
            self.renderer.render(tmp.name,data={"title":"Test Title","metadata":{"description":"test description"}})
            with open(tmp.name,"r") as f:
                assert f.read() == "This is a test template\nTitle : Test Title\nDescription : test description"



