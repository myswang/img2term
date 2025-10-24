import argparse
from curses import KEY_LEFT, KEY_RIGHT
import os
from pathlib import Path
import signal
import numpy as np
from blessed import Terminal
from PIL import Image

term = Terminal()
size_changed = False
img_changed = True
img_idx = 0
file_names = []
images = []
scaled_images = []
rendered_images = []


def load_images(file_path):
    file_formats = {f"{ext.lower()}" for ext in Image.registered_extensions().keys()}
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
    max_height = 2 * (term.height - 1) # allow space for printing at bottom

    # do not scale the image if its smaller than max_width/height
    if img_width <= max_width and img_height <= max_height:
        return img

    width_ratio = max_width / img_width
    height_ratio = max_height / img_height

    scale = min(width_ratio, height_ratio)
    img_width = int(img_width * scale)
    img_height = int(img_height * scale)

    return img.resize((img_width, img_height), Image.Resampling.LANCZOS)


def render_img(img):
    img_arr = np.array(img)
    rgb = img_arr[..., :3].astype(np.float32)
    alpha = img_arr[..., 3:4].astype(np.float32) / 255.0

    composited = rgb * alpha + 255 * (1 - alpha)
    composited = composited.clip(0, 255).astype(np.uint8)

    height, width, _ = composited.shape

    output = []
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
                line.append(term.on_color_rgb(int(tr), int(tg), int(tb)) + " ")
        output.append(term.move_xy(0, y // 2) + "".join(line) + term.normal)

    return "".join(output)


def render_status(file_name, img, img_old):
    status = f"({img_idx+1}/{len(file_names)}) {file_name} | {img.width}x{img.height}"
    if img.width < img_old.width and img.height < img_old.height:
        scale = round(img.width / img_old.width * 100)
        status = status + f" ({scale}% {img_old.width}x{img_old.height})"
    return term.move_xy(0, term.height-1) + status[:term.width]


def render_images():
    global scaled_images, rendered_images
    scaled_images = []
    rendered_images = []
    for img in images:
        scaled_img = resize_img(img)
        scaled_images.append(scaled_img)
        rendered_images.append(render_img(scaled_img))


def on_resize(signum, frame):
    global size_changed
    size_changed = True


def main():

    parser = argparse.ArgumentParser(description="View images in your terminal")
    parser.add_argument("files", nargs="+", help="List of image files")
    args = parser.parse_args()

    if len(args.files) == 0:
        print("img2term: No files specified")
        os._exit(1)

    for file in args.files:
        file_name = str(file)
        load_images(file_name)

    if len(images) == 0:
        print("img2term: No images to display")
        os._exit(1)
    
    global size_changed, img_changed, img_idx
    signal.signal(signal.SIGWINCH, on_resize)

    render_images()

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            if size_changed or img_changed:
                if size_changed:
                    render_images()
                status = render_status(file_names[img_idx], scaled_images[img_idx], images[img_idx])
                output = term.home + term.clear + rendered_images[img_idx] + status + term.clear_eos
                os.write(1, output.encode("utf-8"))
                size_changed = False
                img_changed = False
                    
            val = term.inkey(timeout=0.2)
            if val.lower() == "q":
                break
            elif val.code == KEY_RIGHT and len(images) > 1:
                img_idx += 1
                if img_idx >= len(file_names):
                    img_idx = 0
                img_changed = True
            elif val.code == KEY_LEFT and len(images) > 1:
                img_idx -= 1
                if img_idx < 0:
                    img_idx = len(file_names) - 1
                img_changed = True


if __name__ == "__main__":
    main()
