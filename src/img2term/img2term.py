import os
import signal
import sys
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
    img_height = img.height // 2
    max_width = term.width
    max_height = term.height - 1 # allow space for printing at bottom

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
    for y in range(img.height):
        line = []
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            a /= 255.0
            r = int(r * a + 255 * (1 - a))
            g = int(g * a + 255 * (1 - a))
            b = int(b * a + 255 * (1 - a))
            line.append(term.on_color_rgb(r, g, b) + " ")
        print(term.move_xy(0, y) + "".join(line) + term.normal, end="")


def on_resize(signum, frame):
    global should_render
    should_render = True


def main():
    global should_render
    signal.signal(signal.SIGWINCH, on_resize)

    if len(sys.argv) < 2:
        print("img2term: Please specify a file")
        os._exit(1)
    file_name = str(sys.argv[1])
    img = load_img(file_name)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            if should_render:
                scaled_img = resize_img(img)
                print(term.home + term.clear, end="")
                render_img(scaled_img)
                # print the file name at the bottom
                print(term.move_xy(0, term.height-1) + file_name, end="")
                sys.stdout.flush()
                should_render = False
                    
            val = term.inkey(timeout=0.2)
            if val.lower() == "q":
                break


if __name__ == "__main__":
    main()
