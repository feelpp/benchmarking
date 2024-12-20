""" Tests related to template rendering """

from feelpp.benchmarking.report.renderer import Renderer, RendererFactory
import pytest
import tempfile


class TestRenderer:

    renderer = Renderer("./tests/data/templates/template_test.adoc.j2")

    def test_render(self):
        """ Tests that the renderer correctly renders the template with given data"""
        with tempfile.NamedTemporaryFile(dir = "./tests/data") as tmp:
            self.renderer.render(tmp.name,data={"title":"Test Title","metadata":{"description":"test description"}})
            with open(tmp.name,"r") as f:
                assert f.read() == "This is a test template\nTitle : Test Title\nDescription : test description"


class TestRenderFactory:

    def test_validTemplates(self):
        """ Checks that a renderer is correctly instantiated for valid types."""
        for renderer_type in ["index","benchmark","atomic_overview"]:
            renderer = RendererFactory.create(renderer_type)
            assert hasattr(renderer,"render") and callable(renderer.render)

    def test_invalidTemplate(self):
        """Checks that an exception is thrown when a renderer type is no known"""
        with pytest.raises(NotImplementedError):
            RendererFactory.create("unkown")

