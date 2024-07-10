# -*- coding: utf-8 -*-
"""
Created on Tue Jul 9 17:24:03 2024

@author: Thomas
"""



# wde_map_generator.py

from PIL import Image, ImageDraw, ImageFont

def generate_map(desktop_info, show_grid=False, show_numbers=False, show_legend=False, show_details=False, mark_origin=False):
    """
    Generates a map of the desktop layout based on the provided options.
    
    Args:
    desktop_info (dict): Dictionary containing monitor information.
    show_grid (bool): If True, draw grid lines on the map.
    show_numbers (bool): If True, show coordinate numbers on the grid.
    show_legend (bool): If True, show a legend with monitor information.
    show_details (bool): If True, show detailed coordinates and distances.
    mark_origin (bool): If True, mark the Windows virtual desktop origin with extended lines.
    
    Returns:
    PIL.Image: An image object representing the desktop map.
    """
    # Calculate the total dimensions of the desktop
    all_coords = [coord for monitor in desktop_info["monitors"] for coord in monitor["screen_coords"]]
    min_x, min_y = min(all_coords[::2]), min(all_coords[1::2])
    max_x, max_y = max(all_coords[::2]), max(all_coords[1::2])
    
    # Create the base image
    image = Image.new("RGB", (max_x - min_x, max_y - min_y), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    
    # Draw monitors and taskbars
    for monitor in desktop_info["monitors"]:
        x1, y1, x2, y2 = monitor["screen_coords"]
        draw.rectangle((x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y), outline="blue", fill="lightblue")
        
        tx1, ty1, tx2, ty2 = monitor["taskbar_position"]
        draw.rectangle((tx1 - min_x, ty1 - min_y, tx2 - min_x, ty2 - min_y), outline="red", fill="lightpink")
        
        if show_legend:
            legend_text = f"Monitor: {monitor['device_name']}\nResolution: {x2-x1}x{y2-y1}\nPosition: ({x1}, {y1})"
            draw.text((x1 - min_x + 10, y1 - min_y + 10), legend_text, fill="black", font=font)
    
    # Draw grid and numbers
    if show_grid or show_numbers:
        grid_step = 100
        for i in range(0, max_x - min_x, grid_step):
            if show_grid:
                draw.line((i, 0, i, max_y - min_y), fill="gray", width=1)
            if show_numbers:
                draw.text((i, 0), str(i + min_x), fill="black", font=font)
        for j in range(0, max_y - min_y, grid_step):
            if show_grid:
                draw.line((0, j, max_x - min_x, j), fill="gray", width=1)
            if show_numbers:
                draw.text((0, j), str(j + min_y), fill="black", font=font)
    
    # Show detailed coordinates and distances
    if show_details:
        for monitor in desktop_info["monitors"]:
            x1, y1, x2, y2 = monitor["screen_coords"]
            width, height = x2 - x1, y2 - y1
            draw.text((x1 - min_x + width // 2, y2 - min_y + 5), f"Width: {width}", fill="black", font=font)
            draw.text((x2 - min_x + 5, y1 - min_y + height // 2), f"Height: {height}", fill="black", font=font)

    # Mark the WINDOW's virtual desktop origin with extended lines
    if mark_origin:
        origin_x, origin_y = -min_x, -min_y  # Convert to image coordinates
        draw.line((origin_x, 0, origin_x, image.height), fill="green", width=2)
        draw.line((0, origin_y, image.width, origin_y), fill="green", width=2)
        draw.text((origin_x + 5, origin_y + 5), "Windows Origin", fill="green", font=font)

    return image

def show_mouse_position(map_image, cursor_x, cursor_y):
    """
    Adds cursor crosshair lines to the map at the specified position.
    
    Args:
    map_image (PIL.Image): The base map image.
    cursor_x, cursor_y (int): The current cursor position.
    
    Returns:
    PIL.Image: The map image with the cursor crosshair added.
    """
    draw = ImageDraw.Draw(map_image)
    width, height = map_image.size
    
    # Draw horizontal line
    draw.line((0, cursor_y, width, cursor_y), fill="red", width=1)
    
    # Draw vertical line
    draw.line((cursor_x, 0, cursor_x, height), fill="red", width=1)
    
    return map_image