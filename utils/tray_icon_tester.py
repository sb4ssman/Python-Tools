# -*- coding: utf-8 -*-
"""
Created on Thu May 16 03:55:49 2024

@author: Thomas
"""


# I made this to test how my icons would look in the tray, and enlarged
# You can add more than 3 icons to cycle through
# define your icon, then make sure it's in the list


import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageTk
import threading
import tkinter as tk

def create_icon():
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(image)

    # Draw an open window with a frame

    # Wait lets draw the sun first
    #draw.ellipse([24, 24, 40, 40], outline="black", fill="yellow", width=2)  # Draws a filled ellipse

    # Outer window frame
    draw.rectangle([1, 1, 64, 64], outline="black", fill=None)  
    draw.rectangle([2, 2, 63, 63], outline="black", fill=None)  
    draw.rectangle([3, 3, 62, 62], outline="black", fill=None)  

    draw.line([1, 1, 3, 3], fill="white", width=1)
    draw.line([64, 1, 62, 3], fill="white", width=1)
    draw.line([62, 62, 64, 64], fill="white", width=1)
    draw.line([1, 64, 3, 62], fill="white", width=1)

    # draw inner frame and window sill 
    draw.rectangle([4, 4, 61, 61], outline="white", fill=None)
    draw.rectangle([5, 5, 60, 60], outline="white", fill=None)
    draw.rectangle([6, 6, 59, 59], outline="white", fill=None)

    draw.line([7, 33, 7, 58], fill="black", width=1)  
    draw.line([58, 33, 58, 58], fill="black", width=1)  
    draw.line([4, 61, 6, 59], fill="black", width=1)  
    draw.line([58, 58, 61, 61], fill="black", width=1)  
    draw.line([7, 58, 58, 58], fill="black", width=1)

    # Draw environment
    draw.rectangle([8, 43, 57, 57], fill="green", outline="green")
    draw.rectangle([8, 8, 57, 42], fill="cyan", outline="cyan")


    # Draw the jack holding the window open
    # The platform
    draw.polygon([(20, 36), (34, 22), (46, 24), (32, 38)], fill="yellow", outline="black")  
    draw.polygon([(20, 36), (32, 38), (32, 40), (20, 38)], fill="yellow", outline="black")
    draw.polygon([(32, 38), (46, 24), (46, 26), (32, 40)], fill="yellow", outline="black")

    # The pole
    draw.rectangle([26, 40, 30, 56], fill="yellow", outline="black")

    # The feet
    draw.polygon([(22, 59), (26, 56), (28, 56), (28, 58), (24, 61), (22, 61)], fill="yellow", outline="black")
    draw.polygon([(28, 56), (31, 56), (35, 60), (35, 61), (32, 61), (28, 58)], fill="yellow", outline="black")
    draw.polygon([(31, 55), (35, 55), (37, 56), (37, 59), (35, 59), (33, 57), (31, 57)], fill="yellow", outline="black")


    # The handle
    draw.rectangle([29, 45, 32, 48], fill="black", outline="black")
    draw.polygon([(31, 47), (44, 41), (46, 42), (33, 48)], fill="yellow", outline="black")


    # Draw the open shutter
    draw.line([4, 32, 61, 32], fill="black", width=1)  

    draw.rectangle([4, 4, 61, 31], outline="white", fill=None)  
    draw.rectangle([5, 5, 60, 30], outline="black", fill=None)  
    draw.rectangle([6, 6, 59, 29], outline="white", fill=None)  

    draw.line([33, 7, 33, 28], fill="white", width=1)

    draw.rectangle([7, 7, 32, 28], outline="black", fill=None)
    draw.rectangle([34, 7, 58, 28], outline="black", fill=None)





    return image

# Custom icon drawing script!
def create_icon_sun(width=64, height=64):
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    # Draw a window opened unnecessarily with a hand jack

    # Draw environment
    draw.rectangle([8, 43, 57, 57], fill="green", outline="green")
    draw.rectangle([8, 8, 57, 42], fill="cyan", outline="cyan")

    # I can draw the sun with this
    # draw.ellipse([12, 64, 52, 1], outline="yellow", fill="yellow", width=1)  # Draws a filled ellipse

    # Draw the sun in the upper right corner
    sun_margin = 4
    sun_size = 15
    top_left = (width - sun_margin - sun_size, sun_margin)
    bottom_right = (width - sun_margin, sun_margin + sun_size)
    draw.ellipse([top_left[0], top_left[1], bottom_right[0], bottom_right[1]], outline="yellow", fill="yellow", width=1)


    # Outer window frame
    draw.rectangle([1, 1, 64, 64], outline="black", fill=None)  
    draw.rectangle([2, 2, 63, 63], outline="black", fill=None)  
    draw.rectangle([3, 3, 62, 62], outline="black", fill=None)  

    draw.line([1, 1, 3, 3], fill="white", width=1)
    draw.line([64, 1, 62, 3], fill="white", width=1)
    draw.line([62, 62, 64, 64], fill="white", width=1)
    draw.line([1, 64, 3, 62], fill="white", width=1)

    # draw inner frame and window sill 
    draw.rectangle([4, 4, 61, 61], outline="white", fill=None)
    draw.rectangle([5, 5, 60, 60], outline="white", fill=None)
    draw.rectangle([6, 6, 59, 59], outline="white", fill=None)

    draw.line([7, 33, 7, 58], fill="black", width=1)  
    draw.line([58, 33, 58, 58], fill="black", width=1)  
    draw.line([4, 61, 6, 59], fill="black", width=1)  
    draw.line([58, 58, 61, 61], fill="black", width=1)  
    draw.line([7, 58, 58, 58], fill="black", width=1)




    # Draw the jack holding the window open
    # The platform
    draw.polygon([(20, 36), (34, 22), (46, 24), (32, 38)], fill="yellow", outline="black")  
    draw.polygon([(20, 36), (32, 38), (32, 40), (20, 38)], fill="yellow", outline="black")
    draw.polygon([(32, 38), (46, 24), (46, 26), (32, 40)], fill="yellow", outline="black")

    # The pole
    draw.rectangle([26, 40, 30, 56], fill="yellow", outline="black")

    # The feet
    draw.polygon([(22, 59), (26, 56), (28, 56), (28, 58), (24, 61), (22, 61)], fill="yellow", outline="black")
    draw.polygon([(28, 56), (31, 56), (35, 60), (35, 61), (32, 61), (28, 58)], fill="yellow", outline="black")
    draw.polygon([(31, 55), (35, 55), (37, 56), (37, 59), (35, 59), (33, 57), (31, 57)], fill="yellow", outline="black")


    # The handle
    draw.rectangle([29, 45, 32, 48], fill="black", outline="black")
    draw.polygon([(31, 47), (44, 41), (46, 42), (33, 48)], fill="yellow", outline="black")


    # Draw the open shutter
    draw.line([4, 32, 61, 32], fill="black", width=1)  

    draw.rectangle([4, 4, 61, 31], outline="white", fill=None)  
    draw.rectangle([5, 5, 60, 30], outline="black", fill=None)  
    draw.rectangle([6, 6, 59, 29], outline="white", fill=None)  

    draw.line([33, 7, 33, 28], fill="white", width=1)

    draw.rectangle([7, 7, 32, 28], outline="black", fill=None)
    draw.rectangle([34, 7, 58, 28], outline="black", fill=None)

    # Awesome!
    return image # Return the image, fileapp and trayopener will use it to make icons

# Do it again.
def create_icon_dark(width=64, height=64):
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    # Draw a window opened unnecessarily with a hand jack

    # Draw environment
    draw.rectangle([8, 43, 57, 57], fill="green", outline="green")
    draw.rectangle([8, 8, 57, 42], fill="black", outline="black")
    
    # Draw the sun in the upper right corner
    sun_margin = 4
    sun_size = 15
    top_left = (width - sun_margin - sun_size, sun_margin)
    bottom_right = (width - sun_margin, sun_margin + sun_size)
    draw.ellipse([top_left[0], top_left[1], bottom_right[0], bottom_right[1]], outline="gray", fill="gray", width=1)

    # Outer window frame
    draw.rectangle([1, 1, 64, 64], outline="black", fill=None)  
    draw.rectangle([2, 2, 63, 63], outline="black", fill=None)  
    draw.rectangle([3, 3, 62, 62], outline="black", fill=None)  

    draw.line([1, 1, 3, 3], fill="white", width=1)
    draw.line([64, 1, 62, 3], fill="white", width=1)
    draw.line([62, 62, 64, 64], fill="white", width=1)
    draw.line([1, 64, 3, 62], fill="white", width=1)

    # draw inner frame and window sill 
    draw.rectangle([4, 4, 61, 61], outline="white", fill=None)
    draw.rectangle([5, 5, 60, 60], outline="white", fill=None)
    draw.rectangle([6, 6, 59, 59], outline="white", fill=None)

    draw.line([7, 33, 7, 58], fill="black", width=1)  
    draw.line([58, 33, 58, 58], fill="black", width=1)  
    draw.line([4, 61, 6, 59], fill="black", width=1)  
    draw.line([58, 58, 61, 61], fill="black", width=1)  
    draw.line([7, 58, 58, 58], fill="black", width=1)




    # Draw the jack holding the window open
    # The platform
    draw.polygon([(20, 36), (34, 22), (46, 24), (32, 38)], fill="yellow", outline="black")  
    draw.polygon([(20, 36), (32, 38), (32, 40), (20, 38)], fill="yellow", outline="black")
    draw.polygon([(32, 38), (46, 24), (46, 26), (32, 40)], fill="yellow", outline="black")

    # The pole
    draw.rectangle([26, 40, 30, 56], fill="yellow", outline="black")

    # The feet
    draw.polygon([(22, 59), (26, 56), (28, 56), (28, 58), (24, 61), (22, 61)], fill="yellow", outline="black")
    draw.polygon([(28, 56), (31, 56), (35, 60), (35, 61), (32, 61), (28, 58)], fill="yellow", outline="black")
    draw.polygon([(31, 55), (35, 55), (37, 56), (37, 59), (35, 59), (33, 57), (31, 57)], fill="yellow", outline="black")


    # The handle
    draw.rectangle([29, 45, 32, 48], fill="black", outline="black")
    draw.polygon([(31, 47), (44, 41), (46, 42), (33, 48)], fill="yellow", outline="black")


    # Draw the open shutter
    draw.line([4, 32, 61, 32], fill="black", width=1)  

    draw.rectangle([4, 4, 61, 31], outline="white", fill=None)  
    draw.rectangle([5, 5, 60, 30], outline="black", fill=None)  
    draw.rectangle([6, 6, 59, 29], outline="white", fill=None)  

    draw.line([33, 7, 33, 28], fill="white", width=1)

    draw.rectangle([7, 7, 32, 28], outline="black", fill=None)
    draw.rectangle([34, 7, 58, 28], outline="black", fill=None)

    # Awesome!
    return image # Return the image, fileapp and trayopener will use it to make icons



# List of icon images
icons = [
    create_icon(), 
    create_icon_sun(), 
    create_icon_dark()
]
icon_index = 0


def on_clicked(icon, item):
    if item == "Quit":
        icon.stop()
        if root:
            root.quit()
    else:
        rotate_icon()

def rotate_icon():
    global icon_index, icon
    icon_index = (icon_index + 1) % len(icons)
    icon.icon = icons[icon_index]
    update_window_icons()

def update_window_icons():
    global icon1, icon2, icon3
    icon_image1 = icons[icon_index - 1]
    icon_image1 = icon_image1.resize((128, 128), Image.NEAREST)
    icon1 = ImageTk.PhotoImage(icon_image1)
    canvas1.create_image(0, 0, anchor=tk.NW, image=icon1)

    icon_image2 = icons[icon_index]
    icon_image2 = icon_image2.resize((128, 128), Image.NEAREST)
    icon2 = ImageTk.PhotoImage(icon_image2)
    canvas2.create_image(0, 0, anchor=tk.NW, image=icon2)

    icon_image3 = icons[(icon_index + 1) % len(icons)]
    icon_image3 = icon_image3.resize((128, 128), Image.NEAREST)
    icon3 = ImageTk.PhotoImage(icon_image3)
    canvas3.create_image(0, 0, anchor=tk.NW, image=icon3)

def setup_tray_icon():
    global icon
    menu = pystray.Menu(
        item('Rotate Icon', lambda: on_clicked(icon, 'Rotate')),
        item('Quit', lambda: on_clicked(icon, 'Quit'))
    )

    icon = pystray.Icon("test_icon", icons[icon_index], "Test Icon", menu)
    icon.run(setup=lambda icon: setattr(icon, 'visible', True))

def setup_window():
    global root, canvas1, canvas2, canvas3, icon1, icon2, icon3
    root = tk.Tk()
    root.title("Icon Preview")

    # Create canvas for first icon
    canvas1 = tk.Canvas(root, width=128, height=128)
    canvas1.pack(side=tk.LEFT)
    icon_image1 = icons[icon_index - 1]
    icon_image1 = icon_image1.resize((128, 128), Image.NEAREST)
    icon1 = ImageTk.PhotoImage(icon_image1)
    canvas1.create_image(0, 0, anchor=tk.NW, image=icon1)
    canvas1.bind("<Button-1>", lambda e: rotate_icon())

    # Create canvas for second icon
    canvas2 = tk.Canvas(root, width=128, height=128)
    canvas2.pack(side=tk.LEFT)
    icon_image2 = icons[icon_index]
    icon_image2 = icon_image2.resize((128, 128), Image.NEAREST)
    icon2 = ImageTk.PhotoImage(icon_image2)
    canvas2.create_image(0, 0, anchor=tk.NW, image=icon2)
    canvas2.bind("<Button-1>", lambda e: rotate_icon())

    # Create canvas for third icon
    canvas3 = tk.Canvas(root, width=128, height=128)
    canvas3.pack(side=tk.LEFT)
    icon_image3 = icons[(icon_index + 1) % len(icons)]
    icon_image3 = icon_image3.resize((128, 128), Image.NEAREST)
    icon3 = ImageTk.PhotoImage(icon_image3)
    canvas3.create_image(0, 0, anchor=tk.NW, image=icon3)
    canvas3.bind("<Button-1>", lambda e: rotate_icon())

    root.protocol("WM_DELETE_WINDOW", lambda: on_clicked(icon, "Quit"))
    root.mainloop()

if __name__ == "__main__":
    root = None
    tray_thread = threading.Thread(target=setup_tray_icon)
    tray_thread.start()

    setup_window()




######################
# Sample commands for icon generation

# from PIL import Image, ImageDraw

# def create_icon_image_vX():
#     width, height = 64, 64
#     image = Image.new('RGBA', (width, height), (255, 255, 255, 0))  # Create a new image with a transparent background
#     draw = ImageDraw.Draw(image)

#     # Draw a rectangle
#     # Syntax: draw.rectangle([top_left_x, top_left_y, bottom_right_x, bottom_right_y], outline=color, fill=color, width=line_width)
#     draw.rectangle([4, 4, 60, 60], outline="black", fill=None, width=2)  # Draws a rectangle outline

#     # Draw a filled rectangle
#     draw.rectangle([8, 8, 56, 56], outline="black", fill="white", width=2)  # Draws a filled rectangle

#     # Draw an ellipse (circle or oval)
#     # Syntax: draw.ellipse([top_left_x, top_left_y, bottom_right_x, bottom_right_y], outline=color, fill=color, width=line_width)
#     draw.ellipse([20, 20, 44, 44], outline="black", fill="white", width=2)  # Draws an ellipse outline

#     # Draw a filled ellipse
#     draw.ellipse([24, 24, 40, 40], outline="black", fill="yellow", width=2)  # Draws a filled ellipse

#     # Draw a line
#     # Syntax: draw.line([start_x, start_y, end_x, end_y], fill=color, width=line_width)
#     draw.line([10, 10, 54, 54], fill="black", width=2)  # Draws a line

#     # Draw multiple connected lines
#     # Syntax: draw.line([x1, y1, x2, y2, x3, y3, ...], fill=color, width=line_width)
#     draw.line([10, 54, 32, 10, 54, 54], fill="black", width=2)  # Draws a "V" shape

#     # Draw a polygon (triangle, quadrilateral, etc.)
#     # Syntax: draw.polygon([x1, y1, x2, y2, x3, y3, ...], outline=color, fill=color)
#     draw.polygon([16, 40, 32, 16, 48, 40], outline="black", fill="yellow")  # Draws a filled triangle

#     # Draw an arc (part of an ellipse)
#     # Syntax: draw.arc([top_left_x, top_left_y, bottom_right_x, bottom_right_y], start_angle, end_angle, fill=color, width=line_width)
#     draw.arc([20, 20, 44, 44], start=0, end=180, fill="black", width=2)  # Draws an arc

#     # Draw text
#     # Syntax: draw.text((x, y), "text", fill=color, font=font)
#     draw.text((10, 10), "A", fill="black")  # Draws text "A" at position (10, 10)

#     return image

# # Example usage
# image = create_icon_image_vX()
# image.show()  # This will display the image using the default image viewer
