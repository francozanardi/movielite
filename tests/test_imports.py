"""
Basic import tests to verify syntax and module structure.
"""


def test_import_core():
    """Test importing core modules."""
    from movielite import MediaClip, GraphicClip, VideoClip, ImageClip, AudioClip
    assert MediaClip is not None
    assert GraphicClip is not None
    assert VideoClip is not None
    assert ImageClip is not None
    assert AudioClip is not None


def test_import_writers():
    """Test importing writers."""
    from movielite import VideoWriter
    assert VideoWriter is not None


def test_import_vfx():
    """Test importing vfx module."""
    from movielite import vfx
    assert vfx is not None


def test_import_vtx():
    """Test importing vtx module."""
    from movielite import vtx
    assert vtx is not None


def test_import_afx():
    """Test importing afx module."""
    from movielite import afx
    assert afx is not None


def test_import_enums():
    """Test importing enums."""
    from movielite import VideoQuality
    assert VideoQuality is not None


def test_import_logger():
    """Test importing logger utilities."""
    from movielite import get_logger, set_log_level
    assert get_logger is not None
    assert set_log_level is not None
