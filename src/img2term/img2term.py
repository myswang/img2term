import argparse
from curses import KEY_LEFT, KEY_RIGHT
import os
from pathlib import Path
import signal
import numpy as np
from blessed import Terminal
from PIL import Image

term = Terminal()
file_formats = {f"{ext.lower()}" for ext in Image.registered_extensions().keys()}
resize_detected = False
needs_render = True
show_status = True
img_idx = 0
file_names = []
images = []
scaled_images = {}
rendered_images = {}


def load_images(file_path):
    file = Path(file_path)
    if file.is_dir():
        sub_files = [f for f in file.iterdir() if f.is_file() and f.suffix.lower() in file_formats]
        for sf in sub_files:
            load_img(sf)
    else:
        load_img(file_path)


def load_img(file_name):
    try:
        img = Image.open(file_name).convert("RGBA")
    except FileNotFoundError:
        print(f"img2term: Failed to open file {file_name}")
        os._exit(1)
    except IsADirectoryError:
        print(f"img2term: Failed to open file {file_name}: is a directory")
        os._exit(1)
    file_names.append(file_name)
    images.append(img)

def resize_img(img):
    img_width = img.width
    img_height = img.height
    max_width = term.width
    max_height = 2 * (term.height - 1)
    global show_status
    if not show_status:
        max_height += 2

    # do not scale the image if its smaller than max_width/height
    if img_width <= max_width and img_height <= max_height:
        return img

    width_ratio = max_width / img_width
    height_ratio = max_height / img_height

    scale = min(width_ratio, height_ratio)
    img_width = int(img_width * scale)
    img_height = int(img_height * scale)

    return img.resize((img_width, img_height), Image.Resampling.LANCZOS)


def img_to_array(img):
    img_arr = np.array(img)
    rgb = img_arr[..., :3].astype(np.float32)
    alpha = img_arr[..., 3:4].astype(np.float32) / 255.0

    composited = rgb * alpha + 255 * (1 - alpha)
    composited = composited.clip(0, 255).astype(np.uint8)
    height, width, _ = composited.shape
    return composited, height, width


def render_img(img):
    composited, height, width = img_to_array(img)
    output = []
    mid_x = (term.width - width) // 2
    global show_status
    vy = term.height
    if show_status:
        vy -= 1
    mid_y = (vy * 2 - height) // 4
    for y in range(0, height, 2):
        line = []
        for x in range(width):
            top = composited[y, x]
            if y + 1 < height:
                bottom = composited[y + 1, x]
                tr, tg, tb = top
                br, bg, bb = bottom
                line.append(
                    term.color_rgb(int(tr), int(tg), int(tb)) +
                    term.on_color_rgb(int(br), int(bg), int(bb)) +
                    "▀"
                )
            else:
                tr, tg, tb = top
                line.append(term.color_rgb(int(tr), int(tg), int(tb)) + "▀")

        output.append(term.move_xy(mid_x, mid_y + (y // 2)) + "".join(line) + term.normal)
    return "".join(output)


# render the image at a 1-pixel offset, rather than at whole characters
def render_img_offset(img):
    composited, height, width = img_to_array(img)
    output = []
    mid_x = (term.width - width) // 2
    vy = term.height
    global show_status
    if show_status:
        vy -= 1
    mid_y = (vy * 2 - height) // 4
    y = 0
    screen_y = 0
    while y < height:
        line = []
        for x in range(width):
            top = composited[y, x]
            if y == 0:
                br, bg, bb = top
                line.append(term.color_rgb(int(br), int(bg), int(bb)) + "▄")
            elif y + 1 < height:
                bottom = composited[y + 1, x]
                tr, tg, tb = top
                br, bg, bb = bottom
                line.append(
                    term.color_rgb(int(tr), int(tg), int(tb)) +
                    term.on_color_rgb(int(br), int(bg), int(bb)) +
                    "▀"
                )
            else:
                tr, tg, tb = top
                line.append(term.color_rgb(int(tr), int(tg), int(tb)) + "▀")

        output.append(term.move_xy(mid_x, mid_y + (screen_y // 2)) + "".join(line) + term.normal)
        y += 1
        screen_y += 2
        if y > 1:
            y += 1
    return "".join(output)


def render_status(file_name, img, img_old):
    status = f"({img_idx+1}/{len(file_names)}) {file_name} | {img.width}x{img.height}"
    if img.width < img_old.width and img.height < img_old.height:
        scale = round((img.width * img.height) / (img_old.width * img_old.height) * 100, 1)
        status = status + f" ({scale}% of {img_old.width}x{img_old.height})"
    return term.move_xy(0, term.height-1) + status[:term.width]


def on_resize(signum, frame):
    global resize_detected, needs_render
    resize_detected = True
    needs_render = True


def main():
    parser = argparse.ArgumentParser(prog="img2term", description="view images in your terminal")
    parser.add_argument("file", nargs="+", help="an image file, or a directory containing image files")
    parser.add_argument("-n", "--nostatus", action="store_false", help="hide the status bar")
    args = parser.parse_args()        

    if len(args.file) == 0:
        print("img2term: No files specified")
        os._exit(1)

    for file in args.file:
        file_name = str(file)
        load_images(file_name)

    if len(images) == 0:
        print("img2term: No images to display")
        os._exit(1)
    
    global resize_detected, needs_render, show_status, img_idx, scaled_images, rendered_images
    signal.signal(signal.SIGWINCH, on_resize)

    show_status = args.nostatus

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            if needs_render:
                if resize_detected:
                    scaled_images = {}
                    rendered_images = {}
                    resize_detected = False
                if img_idx not in scaled_images.keys():
                    scaled_images[img_idx] = resize_img(images[img_idx])
                    vy = term.height
                    if show_status:
                        vy -= 1
                    mid_y = (vy * 2 - scaled_images[img_idx].height) // 2
                    if mid_y % 2 != 0:
                        rendered_images[img_idx] = render_img_offset(scaled_images[img_idx])
                    else:
                        rendered_images[img_idx] = render_img(scaled_images[img_idx])
                if show_status:
                    status = render_status(file_names[img_idx], scaled_images[img_idx], images[img_idx])
                else:
                    status = ""
                output = term.home + term.clear + rendered_images[img_idx] + status
                print(output, end="", flush=True)
                needs_render = False
                    
            val = term.inkey(timeout=0.2)
            if val.lower() == "q":
                break
            elif (val.code == KEY_RIGHT or val.lower() == "l") \
                  and len(images) > 1 and img_idx < len(images) - 1:
                img_idx += 1
                needs_render = True
            elif (val.code == KEY_LEFT or val.lower() == "h") \
                  and len(images) > 1 and img_idx > 0:
                img_idx -= 1
                needs_render = True
            elif val.lower() == "s":
                show_status = not show_status
                needs_render = True
                resize_detected = True


if __name__ == "__main__":
    main()
