import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import colorspacious as cs


def generate_random_color(base_color, variability=30):
    return tuple(
        min(max(c + random.randint(-variability, variability), 0), 255)
        for c in base_color
    )


def place_dot(draw, dot_positions, x, y, radius, fill_color):
    dot_position = (x, y, radius)
    if not any(np.hypot(x - dx, y - dy) < radius + dr for dx, dy, dr in dot_positions):
        dot_positions.append(dot_position)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_color)
        return True
    return False


def generate_random_dots(image_size, base_color1, base_color2, number_positions):
    image = Image.new('RGBA', (image_size, image_size))
    draw = ImageDraw.Draw(image)

    dot_positions = []
    dot_sizes = [15, 12, 10, 8, 6, 5]  # Define sizes in descending order

    # First, place the number dots
    for x, y in number_positions:
        while True:
            radius = random.randint(5, 15)  # Random radius for dots
            fill_color = generate_random_color(base_color2 if random.random() < 0.5 else base_color1)
            if place_dot(draw, dot_positions, x, y, radius, fill_color):
                break

    # Now, place the background dots
    for radius in dot_sizes:
        for _ in range(1000):  # Adjust as necessary
            x, y = random.randint(radius, image_size - radius), random.randint(radius, image_size - radius)
            fill_color = generate_random_color(base_color2 if random.random() < 0.5 else base_color1)
            place_dot(draw, dot_positions, x, y, radius, fill_color)

    # Make the image circular by adding a transparency mask
    mask = Image.new('L', (image_size, image_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, image_size, image_size), fill=255)
    image.putalpha(mask)

    return image


def get_number_positions(image_size, number, font_path='arial.ttf'):
    font_size = image_size // 3  # Adjust the font size based on the image size
    font = ImageFont.truetype(font_path, font_size)
    number_image = Image.new('L', (image_size, image_size), 0)
    draw = ImageDraw.Draw(number_image)

    bbox = draw.textbbox((0, 0), str(number), font=font)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (image_size - width) // 2
    y = (image_size - height) // 2
    draw.text((x, y), str(number), fill=255, font=font)

    number_array = np.array(number_image)
    positions = [(j, i) for i in range(number_array.shape[0]) for j in range(number_array.shape[1]) if
                 number_array[i, j] > 0]

    return positions


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
    image_size = 600  # Increase the image size for better clarity

    if blindness_type == 'deuteranopia':
        base_color1 = (0, 100, 0)  # Green
        base_color2 = (255, 0, 0)  # Red
    elif blindness_type == 'protanopia':
        base_color1 = (0, 0, 100)  # Blue
        base_color2 = (255, 0, 0)  # Red
    else:
        raise ValueError("Unsupported color blindness type")

    number_positions = get_number_positions(image_size, number)
    normal_image = generate_random_dots(image_size, base_color1, base_color2, number_positions)

    cb_image = simulate_color_blindness(normal_image, blindness_type)

    return normal_image, cb_image


def combine_images(image1, image2, blindness_type):
    combined_width = image1.width * 2 + 150  # Add space between images
    combined_height = image1.height + 150  # Add space for labels
    combined_image = Image.new('RGB', (combined_width, combined_height), 'white')

    # Add labels
    draw = ImageDraw.Draw(combined_image)
    font = ImageFont.truetype('arial.ttf', 40)
    draw.text((image1.width // 2 - 80, 50), "Normal Vision", fill="black", font=font)
    draw.text((image1.width + 150 + image1.width // 2 - 120, 50), f"Simulated {blindness_type.capitalize()} Vision",
              fill="black", font=font)

    # Paste images
    combined_image.paste(image1.convert('RGB'), (50, 100), image1.split()[3])  # Use alpha channel as mask
    combined_image.paste(image2.convert('RGB'), (image1.width + 150, 100),
                         image2.split()[3])  # Use alpha channel as mask

    return combined_image


# Generate a random two-digit number
number = random.randint(10, 99)
blindness_type = random.choice(['deuteranopia', 'protanopia'])

normal_image, cb_image = create_reverse_ishihara(number, blindness_type)
combined_image = combine_images(normal_image, cb_image, blindness_type)

# Display the combined image
combined_image.show(title='Normal and Colorblind Vision')
