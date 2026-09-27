"""Generates the pixel-art sprite sheets used by examples/games/lane_crosser.py.

Uses only tkinter.PhotoImage -- no Pillow, no external asset pipeline. Run
this script whenever the sprite designs below change:

    python -m examples.assets.generate_lane_crosser_assets

Every sheet shares the engine's default canvas background color (#141928)
so sprites blend into the game window without needing real alpha transparency.
"""

import tkinter as tk

BACKGROUND = '#141928'


def new_sheet(width, height):
    image = tk.PhotoImage(width=width, height=height)
    image.put(BACKGROUND, to=(0, 0, width, height))
    return image


def fill(image, x, y, w, h, color):
    image.put(color, to=(x, y, x + w, y + h))


def draw_frog_idle(image, x0):
    fill(image, x0 + 6, 14, 20, 14, '#33AA33')          # body
    fill(image, x0 + 8, 6, 16, 10, '#2C8C2C')           # head
    fill(image, x0 + 10, 4, 4, 4, '#FFFFFF')            # left eye white
    fill(image, x0 + 18, 4, 4, 4, '#FFFFFF')            # right eye white
    fill(image, x0 + 11, 5, 2, 2, '#111111')            # left pupil
    fill(image, x0 + 19, 5, 2, 2, '#111111')            # right pupil
    fill(image, x0 + 4, 24, 6, 6, '#2C8C2C')            # left leg (tucked)
    fill(image, x0 + 22, 24, 6, 6, '#2C8C2C')           # right leg (tucked)


def draw_frog_hop(image, x0):
    fill(image, x0 + 6, 12, 20, 14, '#33AA33')          # body, raised
    fill(image, x0 + 8, 4, 16, 10, '#2C8C2C')           # head, raised
    fill(image, x0 + 10, 2, 4, 4, '#FFFFFF')
    fill(image, x0 + 18, 2, 4, 4, '#FFFFFF')
    fill(image, x0 + 11, 3, 2, 2, '#111111')
    fill(image, x0 + 19, 3, 2, 2, '#111111')
    fill(image, x0 + 0, 26, 8, 4, '#2C8C2C')            # left leg, extended
    fill(image, x0 + 24, 26, 8, 4, '#2C8C2C')           # right leg, extended


def generate_frog_sheet(path):
    image = new_sheet(64, 32)
    draw_frog_idle(image, 0)
    draw_frog_hop(image, 32)
    image.write(path, format='png')


def draw_car(image, x0, body_color, cabin_color, facing_right):
    fill(image, x0 + 4, 8, 40, 12, body_color)
    cabin_x = x0 + 28 if facing_right else x0 + 6
    fill(image, cabin_x, 4, 14, 8, cabin_color)
    fill(image, x0 + 10, 20, 8, 6, '#111111')
    fill(image, x0 + 30, 20, 8, 6, '#111111')


def generate_car_sheet(path):
    image = new_sheet(192, 28)
    draw_car(image, 0, '#CC3333', '#F0C0C0', facing_right=True)
    draw_car(image, 48, '#CC3333', '#F0C0C0', facing_right=False)
    draw_car(image, 96, '#3366CC', '#C0D0F0', facing_right=True)
    draw_car(image, 144, '#3366CC', '#C0D0F0', facing_right=False)
    image.write(path, format='png')


def draw_log(image, x0, y_offset):
    fill(image, x0 + 4, 10 + y_offset, 88, 10, '#8B5A2B')
    fill(image, x0 + 12, 12 + y_offset, 70, 2, '#6E4620')
    fill(image, x0 + 20, 16 + y_offset, 60, 2, '#6E4620')


def generate_log_sheet(path):
    image = new_sheet(192, 28)
    draw_log(image, 0, 0)
    draw_log(image, 96, 2)
    image.write(path, format='png')


def draw_goal_empty(image, x0):
    fill(image, x0 + 4, 4, 48, 40, '#1A3040')
    fill(image, x0 + 8, 8, 40, 32, '#204558')


def draw_goal_filled(image, x0):
    draw_goal_empty(image, x0)
    fill(image, x0 + 20, 22, 16, 12, '#33AA33')
    fill(image, x0 + 24, 16, 8, 8, '#2C8C2C')


def generate_goal_sheet(path):
    image = new_sheet(112, 48)
    draw_goal_empty(image, 0)
    draw_goal_filled(image, 56)
    image.write(path, format='png')


def main():
    root = tk.Tk()
    root.withdraw()

    generate_frog_sheet('examples/assets/lane_crosser_frog.png')
    generate_car_sheet('examples/assets/lane_crosser_cars.png')
    generate_log_sheet('examples/assets/lane_crosser_logs.png')
    generate_goal_sheet('examples/assets/lane_crosser_goals.png')

    root.destroy()
    print('Generated lane_crosser_frog.png, lane_crosser_cars.png, '
          'lane_crosser_logs.png, lane_crosser_goals.png')


if __name__ == '__main__':
    main()
