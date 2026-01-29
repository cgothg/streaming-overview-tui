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
