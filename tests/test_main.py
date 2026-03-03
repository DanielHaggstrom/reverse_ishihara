import random

import numpy as np
import pytest
from PIL import Image

import main


def test_create_reverse_ishihara_smoke() -> None:
    random.seed(0)
    normal, simulated = main.create_reverse_ishihara(42, "deuteranopia")

    assert normal.mode == "RGBA"
    assert simulated.mode == "RGBA"
    assert normal.size == (main.DEFAULT_CONFIG.image_size, main.DEFAULT_CONFIG.image_size)
    assert simulated.size == normal.size
    assert normal.getpixel((0, 0))[3] == 0
    assert simulated.getpixel((0, 0))[3] == 0


def test_fallback_font_still_renders_number_mask() -> None:
    mask = main.get_number_mask(300, 24, font_path="missing-font.ttf")

    assert mask.any()


def test_simulate_color_blindness_preserves_alpha() -> None:
    image = Image.new("RGBA", (4, 4), (120, 130, 140, 0))
    image.putpixel((1, 1), (120, 130, 140, 255))

    simulated = main.simulate_color_blindness(image, "protanopia")

    assert simulated.mode == "RGBA"
    assert simulated.getchannel("A").tobytes() == image.getchannel("A").tobytes()


def test_simulated_plate_has_stronger_number_separation_than_normal() -> None:
    random.seed(1)
    normal, simulated = main.create_reverse_ishihara(42, "deuteranopia")
    mask = main.get_number_mask(main.DEFAULT_CONFIG.image_size, 42)
    alpha = np.array(normal.getchannel("A")) > 0

    inside_mask = mask & alpha
    outside_mask = (~mask) & alpha

    normal_rgb = np.asarray(normal.convert("RGB"), dtype=np.float32)
    simulated_rgb = np.asarray(simulated.convert("RGB"), dtype=np.float32)

    normal_delta = np.linalg.norm(
        normal_rgb[inside_mask].mean(axis=0) - normal_rgb[outside_mask].mean(axis=0)
    )
    simulated_delta = np.linalg.norm(
        simulated_rgb[inside_mask].mean(axis=0)
        - simulated_rgb[outside_mask].mean(axis=0)
    )

    assert simulated_delta > normal_delta


def test_invalid_blindness_type_raises() -> None:
    with pytest.raises(ValueError):
        main.create_reverse_ishihara(42, "tritanopia")  # type: ignore[arg-type]
