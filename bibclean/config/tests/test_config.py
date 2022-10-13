from bibclean.config import _load_default_config


def test_load_default_config():
    """Test loading of the default configuration."""
    required_fields, keep_fields = _load_default_config()
    assert isinstance(required_fields, dict)
    assert isinstance(keep_fields, dict)
    assert "article" in required_fields
    assert "article" in keep_fields
    # check article
    assert "author" in required_fields["article"]
    assert "journal" in required_fields["article"]
    assert "title" in required_fields["article"]
    assert "year" in required_fields["article"]
    assert "author" in keep_fields["article"]
    assert "journal" in keep_fields["article"]
    assert "month" in keep_fields["article"]
    assert "number" in keep_fields["article"]
    assert "pages" in keep_fields["article"]
    assert "title" in keep_fields["article"]
    assert "volume" in keep_fields["article"]
    assert "year" in keep_fields["article"]
