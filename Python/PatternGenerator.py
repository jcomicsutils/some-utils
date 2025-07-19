import math
from PIL import Image, ImageDraw
import random
import sys

def find_closest_divisor(n, target):
    """Find divisor of n closest to target"""
    divisors = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
    if not divisors:
        return None
    return min(divisors, key=lambda x: abs(x - target))

def generate_irregular_shape(tile_size):
    """Create a random organic shape with boundary awareness"""
    points = []
    num_points = random.randint(5, 8)
    
    x = random.randint(0, tile_size)
    y = random.randint(0, tile_size)
    points.append((x, y))
    
    for _ in range(num_points - 1):
        dx = random.randint(-tile_size//2, tile_size//2)
        dy = random.randint(-tile_size//2, tile_size//2)
        new_x = (x + dx) % tile_size
        new_y = (y + dy) % tile_size
        points.append((new_x, new_y))
        x, y = new_x, new_y
    
    return points

def draw_tile(tile_size, palette, used_colors):
    """Create a tile with mixed regular and irregular shapes"""
    tile = Image.new('RGB', (tile_size, tile_size), 'white')
    draw = ImageDraw.Draw(tile)
    
    elements = [
        'rotated_square', 
        'diagonal_stripe',
        'interlocking_circles',
        'triangle_pattern',
        'organic_blob',
        'bezier_curve'
    ]
    
    element_count = min(len(palette), random.randint(3, len(palette)))
    
    for _ in range(element_count):
        elem = random.choice(elements)
        color = random.choice(palette)
        used_colors.add(color)
        
        min_size = max(4, tile_size // 8)
        max_size = max(8, tile_size // 4)
        size = random.randint(min_size, max_size)
        
        if elem == 'rotated_square':
            angle = random.randint(0, 180)
            square_size = random.randint(tile_size//4, tile_size//2)
            square = Image.new('RGB', (square_size, square_size), color)
            square = square.rotate(angle, expand=0)
            tile.paste(square, (
                random.randint(0, tile_size-square_size),
                random.randint(0, tile_size-square_size)
            ))
            
        elif elem == 'diagonal_stripe':
            stripe_width = max(1, tile_size // 20)
            for i in range(-1, 2):
                start = (i*tile_size, 0)
                end = ((i+1)*tile_size, tile_size)
                draw.line([start, end], fill=color, width=stripe_width)
                
        elif elem == 'interlocking_circles':
            circle_size = random.randint(tile_size//6, tile_size//3)
            for x in [0, tile_size]:
                for y in [0, tile_size]:
                    draw.ellipse([
                        x-circle_size, y-circle_size,
                        x+circle_size, y+circle_size
                    ], outline=color)
                    
        elif elem == 'triangle_pattern':
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    x = tile_size//2 + dx * tile_size
                    y = tile_size//2 + dy * tile_size
                    draw.polygon([
                        (x, y - size),
                        (x + size, y + size),
                        (x - size, y + size)
                    ], fill=color)
        
        elif elem == 'organic_blob':
            points = generate_irregular_shape(tile_size)
            draw.polygon(points, fill=color)
            
        elif elem == 'bezier_curve':
            # Manual Bézier curve implementation
            p0 = (random.randint(0, tile_size), random.randint(0, tile_size))
            p1 = (random.randint(0, tile_size), random.randint(0, tile_size))
            p2 = (random.randint(0, tile_size), random.randint(0, tile_size))
            p3 = (random.randint(0, tile_size), random.randint(0, tile_size))
            
            curve_points = []
            steps = 50
            for t in range(steps + 1):
                t_norm = t / steps
                x = (1 - t_norm)**3 * p0[0] + 3 * (1 - t_norm)**2 * t_norm * p1[0] + 3 * (1 - t_norm) * t_norm**2 * p2[0] + t_norm**3 * p3[0]
                y = (1 - t_norm)**3 * p0[1] + 3 * (1 - t_norm)**2 * t_norm * p1[1] + 3 * (1 - t_norm) * t_norm**2 * p2[1] + t_norm**3 * p3[1]
                curve_points.append((int(x), int(y)))
            
            draw.line(curve_points, fill=color, width=random.randint(2, 5))

    return tile


# Get user inputs
try:
    image_size = int(input("Enter image size (pixels, min 256): "))
    if image_size < 256:
        raise ValueError("Image size must be at least 256 pixels")
    
    target_tile_size = int(input("Enter approximate tile size: "))
    color_count = int(input("Enter number of colors (0 for random): "))
    if color_count < 0:
        raise ValueError("Color count must be 0 or positive integer")
    
    # Generate palette
    if color_count == 0:
        color_count = random.randint(5, 12)
    palette = [
        (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for _ in range(color_count)
    ]
    
    # Calculate valid tile size
    min_tile = 64
    max_tile = image_size // 4
    valid_tile = find_closest_divisor(image_size, target_tile_size)
    final_tile = max(min_tile, min(valid_tile, max_tile)) if valid_tile else min_tile
    
    print(f"Using tile size: {final_tile} with {color_count} colors")

except ValueError as e:
    print(f"Invalid input: {e}")
    sys.exit()

# Generate pattern with multiple unique tiles
pattern = Image.new('RGB', (image_size, image_size))
num_tiles = image_size // final_tile
used_colors = set()

# Create multiple unique tiles
tile_variations = 4
tiles = []
for _ in range(tile_variations):
    tiles.append(draw_tile(final_tile, palette, used_colors))

# Verify color usage
used_count = len(used_colors)
if used_count < color_count:
    print(f"Warning: Only used {used_count}/{color_count} colors. Try:")
    print("- Larger tile size")
    print("- More tile variations")
    print("- Fewer colors")

# Create final pattern
for x in range(num_tiles):
    for y in range(num_tiles):
        tile_index = (x + y) % tile_variations
        pattern.paste(tiles[tile_index], (x*final_tile, y*final_tile))

# Save image
name = f'cover_{random.randint(0,9999999)}.png'
pattern.save(name)
print(f"Repeating pattern saved as {name}")