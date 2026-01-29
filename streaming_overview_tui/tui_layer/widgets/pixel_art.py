from PIL import Image
from rich.style import Style
from rich.text import Text


def image_to_half_blocks(image: Image.Image, width: int, height: int) -> Text:
    """Convert a PIL Image to Rich Text using half-block characters.

    Each character cell represents 2 vertical pixels using the half-block character.
    The top pixel is the background color, bottom pixel is foreground color.

    Args:
        image: PIL Image to convert (will be resized)
        width: Target width in characters
        height: Target height in characters (each char = 2 pixels)

    Returns:
        Rich Text object with styled half-block characters
    """
    # Resize image to target pixel dimensions
    pixel_height = height * 2  # 2 vertical pixels per character
    resized = image.resize((width, pixel_height), Image.Resampling.NEAREST)

    # Ensure RGB mode
    if resized.mode != "RGB":
        resized = resized.convert("RGB")

    pixels = resized.load()
    text = Text()

    for char_row in range(height):
        if char_row > 0:
            text.append("\n")

        for col in range(width):
            # Top pixel (background) and bottom pixel (foreground)
            top_y = char_row * 2
            bottom_y = top_y + 1

            top_color = pixels[col, top_y]
            bottom_color = pixels[col, bottom_y]

            # Convert RGB tuples to hex colors
            bg_hex = "#{:02x}{:02x}{:02x}".format(*top_color)
            fg_hex = "#{:02x}{:02x}{:02x}".format(*bottom_color)

            style = Style(color=fg_hex, bgcolor=bg_hex)
            text.append("\u2584", style=style)

    return text
