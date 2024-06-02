import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import colorspacious as cs


def generate_random_dots(image_size, num_dots, color1, color2):
    image = Image.new('RGBA', (image_size, image_size))
    draw = ImageDraw.Draw(image)

    for _ in range(num_dots):
        x, y = random.randint(0, image_size - 1), random.randint(0, image_size - 1)
        radius = random.randint(3, 7)  # Random radius for dots
        fill_color = color2 if random.random() < 0.5 else color1
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_color)

    # Make the image circular by adding a transparency mask
    mask = Image.new('L', (image_size, image_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, image_size, image_size), fill=255)
    image.putalpha(mask)

    return image


def embed_number(image, number, font_path='arial.ttf', font_size=80, color1=(255, 0, 0), color2=(0, 255, 0)):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), str(number), font=font)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (image.width - width) // 2
    y = (image.height - height) // 2
    draw.text((x, y), str(number), fill=color2, font=font)

    return image


def simulate_color_blindness(image, blindness_type):
    rgb_array = np.array(image.convert('RGB')) / 255.0
    if blindness_type == 'deuteranopia':
        cb_type = 'deuteranomaly'
    elif blindness_type == 'protanopia':
        cb_type = 'protanomaly'
    else:
        raise ValueError("Unsupported color blindness type")

    cb_space = cs.cspace_convert(rgb_array, {"name": "sRGB1"},
                                 {"name": "sRGB1+CVD", "cvd_type": cb_type, "severity": 100})
    cb_image = Image.fromarray((cb_space * 255).astype(np.uint8))

    # Ensure cb_image has an alpha channel
    cb_image = cb_image.convert('RGBA')
    alpha = image.split()[3]
    cb_image.putalpha(alpha)

    return cb_image


def create_reverse_ishihara(number, blindness_type):
    image_size = 400
    num_dots = 2000  # Adjusted number of dots

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


def combine_images(image1, image2, blindness_type):
    combined_width = image1.width * 2 + 100  # Add space between images
    combined_height = image1.height + 100  # Add space for labels
    combined_image = Image.new('RGB', (combined_width, combined_height), 'white')

    # Add labels
    draw = ImageDraw.Draw(combined_image)
    font = ImageFont.truetype('arial.ttf', 40)
    draw.text((image1.width // 2 - 80, 20), "Normal Vision", fill="black", font=font)
    draw.text((image1.width + 100 + image1.width // 2 - 120, 20), f"Simulated {blindness_type.capitalize()} Vision",
              fill="black", font=font)

    # Paste images
    combined_image.paste(image1.convert('RGB'), (50, 100), image1.split()[3])  # Use alpha channel as mask
    combined_image.paste(image2.convert('RGB'), (image1.width + 100, 100),
                         image2.split()[3])  # Use alpha channel as mask

    return combined_image


# Generate a random two-digit number
number = random.randint(10, 99)
blindness_type = 'deuteranopia'

normal_image, cb_image = create_reverse_ishihara(number, blindness_type)
combined_image = combine_images(normal_image, cb_image, blindness_type)

# Display the combined image
combined_image.show(title='Normal and Colorblind Vision')
