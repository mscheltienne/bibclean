from bibclean.config import _load_default_config


def test_load_default_config():
    """Test loading of the default configuration."""
    required_fields = _load_default_config()
    assert isinstance(required_fields, dict)
    assert "article" in required_fields
    # check article
    assert "author" in required_fields["article"]
    assert "journal" in required_fields["article"]
    assert "title" in required_fields["article"]
    assert "year" in required_fields["article"]
