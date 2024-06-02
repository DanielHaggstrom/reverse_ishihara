import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import colorspacious as cs


def generate_random_dots(image_size, num_dots, color1, color2):
    image = Image.new('RGB', (image_size, image_size), color1)
    draw = ImageDraw.Draw(image)

    for _ in range(num_dots):
        x, y = random.randint(0, image_size - 1), random.randint(0, image_size - 1)
        draw.point((x, y), fill=color2)

    return image


def embed_number(image, number, font_path='arial.ttf', font_size=40, color1=(255, 0, 0), color2=(0, 255, 0)):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), str(number), font=font)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (image.width - width) // 2
    y = (image.height - height) // 2
    draw.text((x, y), str(number), fill=color2, font=font)

    return image


def simulate_color_blindness(image, blindness_type):
    rgb_array = np.array(image) / 255.0
    if blindness_type == 'deuteranopia':
        cb_type = 'deuteranomaly'
    elif blindness_type == 'protanopia':
        cb_type = 'protanomaly'
    else:
        raise ValueError("Unsupported color blindness type")

    cb_space = cs.cspace_convert(rgb_array, {"name": "sRGB1"},
                                 {"name": "sRGB1+CVD", "cvd_type": cb_type, "severity": 100})
    return Image.fromarray((cb_space * 255).astype(np.uint8))


def create_reverse_ishihara(number, blindness_type):
    image_size = 400
    num_dots = 10000

    if blindness_type == 'deuteranopia':
        color1 = (0, 100, 0)  # Green
        color2 = (255, 0, 0)  # Red
    elif blindness_type == 'protanopia':
        color1 = (0, 0, 100)  # Blue
        color2 = (255, 0, 0)  # Red
    else:
        raise ValueError("Unsupported color blindness type")

    normal_image = generate_random_dots(image_size, num_dots, color1, color2)
    normal_image = embed_number(normal_image, number, color1=color1, color2=color2)

    cb_image = simulate_color_blindness(normal_image, blindness_type)

    return normal_image, cb_image


# Example usage
number = 42
blindness_type = 'deuteranopia'
normal_image, cb_image = create_reverse_ishihara(number, blindness_type)

# Display both images
normal_image.show(title='Normal Vision')
cb_image.show(title=f'Simulated {blindness_type.capitalize()} Vision')
