import os
import signal
import sys
import numpy as np
from blessed import Terminal
from PIL import Image

term = Terminal()
should_render = True

def load_img(file_name):
    try:
        img = Image.open(file_name).convert("RGBA")
    except FileNotFoundError:
        print(f"img2term: Failed to open file {file_name}")
        os._exit(1)

    return img


def resize_img(img):
    img_width = img.width
    img_height = img.height
    max_width = term.width
    max_height = 2 * (term.height - 1) # allow space for printing at bottom

    # do not scale the image if its smaller than max_width/height
    if img_width <= max_width and img_height <= max_height:
        return img

    img_aspect = img_width / img_height
    term_aspect = max_width / max_height
    scale = 1.0

    if img_aspect > term_aspect:
        scale = max_width / img_width
    else:
        scale = max_height / img_height

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

    sys.stdout.write("".join(output))


def render_status(file_name, img, img_old):
    status = f"{file_name} | {img.width}x{img.height}"
    if img.width < img_old.width and img.height < img_old.height:
        scale = round(img.width / img_old.width * 100)
        status = status + f" ({scale}% {img_old.width}x{img_old.height})"
    print(term.move_xy(0, term.height-1) + status[:term.width], end="")


def on_resize(signum, frame):
    global should_render
    should_render = True


def main():
    global should_render
    signal.signal(signal.SIGWINCH, on_resize)

    if len(sys.argv) < 2:
        print("img2term: Please specify a file name")
        os._exit(1)
    file_name = str(sys.argv[1])
    img = load_img(file_name)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            if should_render:
                scaled_img = resize_img(img)
                print(term.home + term.clear, end="")
                render_img(scaled_img)
                render_status(file_name, scaled_img, img)
                sys.stdout.flush()
                should_render = False
                    
            val = term.inkey(timeout=0.2)
            if val.lower() == "q":
                break


if __name__ == "__main__":
    main()
