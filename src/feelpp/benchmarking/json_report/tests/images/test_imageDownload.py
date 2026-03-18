import pytest
from feelpp.benchmarking.json_report.schemas.jsonReport import ImageNode
from pydantic import ValidationError

class TestImageNodeDownloadFeature:
    """Tests for image node download functionality"""

    def test_image_node_with_id(self):
        """Test ImageNode with optional id field for cross-referencing"""
        node = ImageNode(
            type="image",
            src="https://example.com/diagram.png",
            id="architecture_diagram",
            caption="System Architecture"
        )
        assert node.id == "architecture_diagram"
        assert node.caption == "System Architecture"

    def test_image_node_remote_false_explicit(self):
        """Test ImageNode with explicit is_remote=False"""
        node = ImageNode(type="image", src="./images/test.png", is_remote=False)
        assert node.is_remote is False

    def test_image_node_download_image_local_warning(self):
        """Test that downloadImage warns when used on local image"""
        node = ImageNode(type="image", src="local.png", is_remote=False)
        with pytest.warns(UserWarning):
            result = node.downloadImage()
        assert result == "local.png"

    def test_image_node_download_image_local_returns_src(self):
        """Test downloadImage returns src for local images"""
        node = ImageNode(type="image", src="path/to/image.png", is_remote=False)
        with pytest.warns(UserWarning):
            result = node.downloadImage()
        assert result == "path/to/image.png"

    def test_image_node_validation(self):
        """Test ImageNode validation"""
        with pytest.raises(ValidationError):
            ImageNode.model_validate({"type": "image"})

    def test_image_download(self, tmp_path):
        """Test downloadImage downloads remote image to temporary directory"""
        from unittest.mock import patch, MagicMock

        node = ImageNode(type="image", src="https://example.com/test.png", is_remote=True)

        # Mock the actual HTTP download to avoid network calls
        mock_response = MagicMock()
        mock_response.content = b"PNG_DATA_HERE"
        mock_response.status_code = 200

        with patch('requests.get', return_value=mock_response):
            result = node.downloadImage(str(tmp_path))

        assert result == "test.png"

        downloaded_file = tmp_path / "test.png"
        assert downloaded_file.exists()
        assert downloaded_file.read_bytes() == b"PNG_DATA_HERE"
