from fints.hhd.flicker import terminal_flicker_unix

from io import BytesIO
from PIL import Image


def encoded_png_to_unicode_qr(encoded_png, scaling_factor=1.0):
    image = Image.open(BytesIO(encoded_png))
    new_size = (int(image.width * scaling_factor), int(image.height * scaling_factor))
    image = image.resize(new_size, Image.LANCZOS)
    image = image.convert("L")

    empty_empty = " "
    empty_full = "▄"
    full_empty = "▀"
    full_full = "█"
    char_matrix = [[empty_empty, empty_full], [full_empty, full_full]]

    def pixel_to_code(pixel):
        return int(pixel / 255)

    unicode_str = ""
    for y in range(0, image.height, 2):
        for x in range(image.width):
            up = pixel_to_code(image.getpixel((x, y)))
            if y == image.height - 1:
                down = 0
            else:
                down = pixel_to_code(image.getpixel((x, y + 1)))
            unicode_char = char_matrix[up][down]
            unicode_str += unicode_char
        unicode_str += "\n"
    return unicode_str


def challenge_matrix_to_unicode_qr(challenge_matrix, scaling_factor=0.5):
    mime_type, encoded_png = challenge_matrix
    if mime_type == "image/png":
        return encoded_png_to_unicode_qr(encoded_png, scaling_factor)
    raise NotImplementedError(mime_type)


def ask_for_tan(f, response):
    print("A TAN is required")
    print(response.challenge)
    if getattr(response, "challenge_hhduc", None):
        try:
            terminal_flicker_unix(response.challenge_hhduc)
        except KeyboardInterrupt:
            pass
    elif getattr(response, "challenge_matrix", None):
        print("Scan this qr code")
        print(challenge_matrix_to_unicode_qr(response.challenge_matrix))
    if response.decoupled:
        tan = input("Please press enter after confirming the transaction in your app:")
    else:
        tan = input("Please enter TAN:")

    if f is None:
        return tan
    return f.send_tan(response, tan)

