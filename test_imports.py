"""
Quick test to verify all imports work correctly
"""

def test_core_imports():
    """Test that core modules can be imported"""
    print("Testing core imports...")
    from movielite import (
        Clip,
        VideoClip,
        ImageClip,
        AudioClip,
        TextClip,
        CompositeClip,
        VideoComposition,
        concatenate_videoclips,
        concatenate_audioclips,
        VideoQuality,
        get_logger,
        set_log_level,
    )
    print("✓ All core imports successful")


def test_fx_imports():
    """Test that fx modules can be imported"""
    print("Testing fx imports...")
    from movielite.fx import (
        fade_in,
        fade_out,
        resize,
        audio_fade_in,
        audio_fade_out,
        volumex,
    )
    print("✓ All fx imports successful")


def test_basic_instantiation():
    """Test that basic objects can be created"""
    print("Testing basic instantiation...")
    from movielite import ImageClip, CompositeClip, AudioClip
    from movielite.core import VideoQuality

    # Test ImageClip from color
    img = ImageClip.from_color((255, 0, 0), (100, 100), duration=1)
    assert img.size == (100, 100)
    print("✓ ImageClip.from_color works")

    # Test CompositeClip
    composite = CompositeClip([img], size=(1920, 1080))
    assert composite.size == (1920, 1080)
    print("✓ CompositeClip works")

    # Test VideoQuality enum
    assert VideoQuality.MIDDLE.value == "middle"
    print("✓ VideoQuality enum works")

    print("✓ All basic instantiation tests passed")


def test_chainable_methods():
    """Test that methods return self for chaining"""
    print("Testing chainable methods...")
    from movielite import ImageClip

    img = ImageClip.from_color((255, 0, 0), (100, 100))
    result = img.set_position((10, 10)).set_opacity(0.5).set_scale(0.8)

    # Should be the same object
    assert result is img
    print("✓ Chainable methods work")


if __name__ == "__main__":
    print("=" * 50)
    print("movielite Import and Basic Tests")
    print("=" * 50)

    try:
        test_core_imports()
        test_fx_imports()
        test_basic_instantiation()
        test_chainable_methods()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
