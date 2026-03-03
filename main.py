from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Final, Literal

import colorspacious as cs
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BlindnessType = Literal["deuteranopia", "protanopia"]


@dataclass(frozen=True)
class Palette:
    foreground: tuple[int, int, int]
    background: tuple[int, int, int]
    simulation_type: str


@dataclass(frozen=True)
class RenderConfig:
    image_size: int = 600
    grid_step: int = 5
    dot_sizes: tuple[int, ...] = (15, 12, 10, 8, 6, 5)
    attempts_per_size: int = 8000
    color_variability: int = 16
    label_font_size: int = 38
    margin: int = 40
    label_gap: int = 24
    gutter: int = 40


DEFAULT_CONFIG: Final = RenderConfig()
FONT_CANDIDATES: Final[tuple[str, ...]] = (
    "arial.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
)
PALETTES: Final[dict[BlindnessType, Palette]] = {
    # These pairs are intentionally close in normal RGB space and separate more
    # strongly in the simulated view, which supports the reverse-Ishihara effect.
    "deuteranopia": Palette(
        foreground=(58, 57, 108),
        background=(52, 89, 98),
        simulation_type="deuteranomaly",
    ),
    "protanopia": Palette(
        foreground=(224, 232, 244),
        background=(240, 229, 244),
        simulation_type="protanomaly",
    ),
}


def generate_random_color(
    base_color: tuple[int, int, int],
    variability: int = DEFAULT_CONFIG.color_variability,
) -> tuple[int, int, int]:
    return tuple(
        min(max(channel + random.randint(-variability, variability), 0), 255)
        for channel in base_color
    )


def create_grid(image_size: int, grid_step: int) -> np.ndarray:
    cells = math.ceil(image_size / grid_step)
    return np.zeros((cells, cells), dtype=bool)


def can_place_dot(
    grid: np.ndarray,
    x: int,
    y: int,
    radius: int,
    grid_step: int,
) -> bool:
    grid_x = x // grid_step
    grid_y = y // grid_step
    span = max(1, math.ceil(radius / grid_step))
    x0 = max(0, grid_x - span)
    x1 = min(grid.shape[1], grid_x + span + 1)
    y0 = max(0, grid_y - span)
    y1 = min(grid.shape[0], grid_y + span + 1)
    return not grid[y0:y1, x0:x1].any()


def place_dot(
    draw: ImageDraw.ImageDraw,
    grid: np.ndarray,
    x: int,
    y: int,
    radius: int,
    fill_color: tuple[int, int, int],
    grid_step: int,
) -> None:
    grid_x = x // grid_step
    grid_y = y // grid_step
    span = max(1, math.ceil(radius / grid_step))
    x0 = max(0, grid_x - span)
    x1 = min(grid.shape[1], grid_x + span + 1)
    y0 = max(0, grid_y - span)
    y1 = min(grid.shape[0], grid_y + span + 1)
    grid[y0:y1, x0:x1] = True
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_color)


def get_palette(blindness_type: BlindnessType) -> Palette:
    try:
        return PALETTES[blindness_type]
    except KeyError as error:
        raise ValueError(
            f"Unsupported color blindness type: {blindness_type!r}"
        ) from error


def load_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [font_path] if font_path else []
    candidates.extend(FONT_CANDIDATES)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue

    return ImageFont.load_default(size=size)


def get_number_mask(
    image_size: int,
    number: int,
    font_path: str | None = None,
) -> np.ndarray:
    font = load_font(image_size // 3, font_path)
    number_image = Image.new("L", (image_size, image_size), 0)
    draw = ImageDraw.Draw(number_image)

    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (image_size - width) // 2 - bbox[0]
    y = (image_size - height) // 2 - bbox[1]
    draw.text((x, y), text, fill=255, font=font)

    return np.array(number_image) > 0


def is_inside_circle(x: int, y: int, radius: int, image_size: int) -> bool:
    center = (image_size - 1) / 2
    max_distance = center - radius
    return ((x - center) ** 2 + (y - center) ** 2) <= max_distance**2


def generate_random_dots(
    image_size: int,
    palette: Palette,
    number_mask: np.ndarray,
    config: RenderConfig = DEFAULT_CONFIG,
) -> Image.Image:
    image = Image.new("RGBA", (image_size, image_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    grid = create_grid(image_size, config.grid_step)

    for radius in config.dot_sizes:
        for _ in range(config.attempts_per_size):
            x = random.randint(radius, image_size - radius - 1)
            y = random.randint(radius, image_size - radius - 1)
            if not is_inside_circle(x, y, radius, image_size):
                continue
            if not can_place_dot(grid, x, y, radius, config.grid_step):
                continue

            base_color = palette.foreground if number_mask[y, x] else palette.background
            fill_color = generate_random_color(base_color, config.color_variability)
            place_dot(draw, grid, x, y, radius, fill_color, config.grid_step)

    mask = Image.new("L", (image_size, image_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, image_size - 1, image_size - 1), fill=255)
    image.putalpha(mask)
    return image


def simulate_color_blindness(
    image: Image.Image,
    blindness_type: BlindnessType,
) -> Image.Image:
    rgb_array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    palette = get_palette(blindness_type)

    simulated = cs.cspace_convert(
        rgb_array,
        {"name": "sRGB1"},
        {
            "name": "sRGB1+CVD",
            "cvd_type": palette.simulation_type,
            "severity": 100,
        },
    )
    simulated = np.nan_to_num(simulated, nan=0.0, posinf=1.0, neginf=0.0)
    simulated = np.clip(simulated, 0.0, 1.0)

    simulated_image = Image.fromarray(
        np.rint(simulated * 255).astype(np.uint8),
        mode="RGB",
    ).convert("RGBA")
    simulated_image.putalpha(image.getchannel("A"))
    return simulated_image


def create_reverse_ishihara(
    number: int,
    blindness_type: BlindnessType,
    config: RenderConfig = DEFAULT_CONFIG,
    font_path: str | None = None,
) -> tuple[Image.Image, Image.Image]:
    palette = get_palette(blindness_type)
    number_mask = get_number_mask(config.image_size, number, font_path)
    normal_image = generate_random_dots(config.image_size, palette, number_mask, config)
    simulated_image = simulate_color_blindness(normal_image, blindness_type)
    return normal_image, simulated_image


def combine_images(
    image1: Image.Image,
    image2: Image.Image,
    blindness_type: BlindnessType,
    config: RenderConfig = DEFAULT_CONFIG,
    font_path: str | None = None,
) -> Image.Image:
    font = load_font(config.label_font_size, font_path)
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1), "white"))
    labels = (
        "Normal Vision",
        f"Simulated {blindness_type.capitalize()} Vision",
    )
    label_heights = []
    label_widths = []
    for label in labels:
        bbox = scratch.textbbox((0, 0), label, font=font)
        label_widths.append(bbox[2] - bbox[0])
        label_heights.append(bbox[3] - bbox[1])

    label_height = max(label_heights)
    combined_width = (
        image1.width + image2.width + (config.margin * 2) + config.gutter
    )
    combined_height = (
        max(image1.height, image2.height)
        + (config.margin * 2)
        + label_height
        + config.label_gap
    )
    combined_image = Image.new("RGB", (combined_width, combined_height), "white")
    draw = ImageDraw.Draw(combined_image)

    left_x = config.margin
    right_x = config.margin + image1.width + config.gutter
    image_y = config.margin + label_height + config.label_gap

    draw.text(
        (left_x + (image1.width - label_widths[0]) // 2, config.margin),
        labels[0],
        fill="black",
        font=font,
    )
    draw.text(
        (right_x + (image2.width - label_widths[1]) // 2, config.margin),
        labels[1],
        fill="black",
        font=font,
    )

    combined_image.paste(image1.convert("RGB"), (left_x, image_y), image1.getchannel("A"))
    combined_image.paste(image2.convert("RGB"), (right_x, image_y), image2.getchannel("A"))
    return combined_image


def main() -> int:
    number = random.randint(10, 99)
    blindness_type = random.choice(tuple(PALETTES))
    normal_image, simulated_image = create_reverse_ishihara(number, blindness_type)
    combined_image = combine_images(normal_image, simulated_image, blindness_type)
    combined_image.show(title=f"Reverse Ishihara - {number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
