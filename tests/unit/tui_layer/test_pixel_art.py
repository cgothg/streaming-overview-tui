from PIL import Image
from rich.text import Text

from streaming_overview_tui.tui_layer.widgets.pixel_art import image_to_half_blocks


class TestImageToHalfBlocks:
    def test_solid_red_image_produces_uniform_output(self):
        """A solid red image should produce all red half-blocks."""
        # 4x4 pixel red image -> 4 wide x 2 tall in characters
        img = Image.new("RGB", (4, 4), color=(255, 0, 0))
        result = image_to_half_blocks(img, width=4, height=2)

        assert isinstance(result, Text)
        # Should have 2 lines (2 char rows)
        lines = str(result).split("\n")
        assert len(lines) == 2
        # Each line should have 4 half-block characters
        assert all(len(line) == 4 for line in lines)
        # All characters should be the lower half-block
        assert all(c == "▄" for line in lines for c in line)

    def test_two_color_vertical_stripe(self):
        """Top half red, bottom half blue should have different fg/bg colors."""
        img = Image.new("RGB", (2, 4), color=(255, 0, 0))
        pixels = img.load()
        # Bottom 2 rows are blue
        for x in range(2):
            for y in range(2, 4):
                pixels[x, y] = (0, 0, 255)

        result = image_to_half_blocks(img, width=2, height=2)
        plain = str(result)

        # First row: red top, red bottom (same color)
        # Second row: red top, blue bottom (different colors)
        lines = plain.split("\n")
        assert len(lines) == 2
        assert all(c == "▄" for line in lines for c in line)

    def test_respects_target_dimensions(self):
        """Output should match requested width and height."""
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        result = image_to_half_blocks(img, width=12, height=18)
        lines = str(result).split("\n")

        assert len(lines) == 18
        assert all(len(line) == 12 for line in lines)
