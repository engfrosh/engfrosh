import qrcode
import qrcode.constants
import qrcode.image.svg
from qrcode.image.styledpil import StyledPilImage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random

COUNT = 100
URLS = [
    "https://www.youtube.com/watch?v=xvFZjo5PgG0",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=_XtvecV4ips",
    "https://www.youtube.com/watch?v=Ct6BUPvE2sM",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://www.youtube.com/watch?v=47ntBElzaWk",
    "https://www.youtube.com/watch?v=q0GdxdI4RFE",
    ]
TEXTS = [
    "dellorkcir",
    "sheRedOnMyHerringTillIAmMisled",
    "blueSpiritBestSpirit",
    "whoIsRick?",
    "IAmEnginearingMyLimit",
    "bananaMan",
    "joinTheCSESTechTeam",
    "whatIsABook",
    "TakeTheElevator",
    "DontTouchTheHelicopter",
    "LarryIsALobster",
    "ElbowsInMySocks",
    "PleasantOrange",
    "nightmare",
    "PurpleCrocs",
    "backagain",
    "whatisagym",
    "orderInTheFoodCourt",
    "stonks",
    "bigLadder"
    ]

for num in range(COUNT):
    url = URLS[random.randrange(len(URLS))]
    text = TEXTS[random.randrange(len(TEXTS))]
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(url)
    qr.make(fit=True)

    blob = BytesIO()
    STYLE_IMAGE_PATH = "engfrosh_site/SpiritX.png"
    USE_IMAGE = True
    if USE_IMAGE:
        img = qr.make_image(image_factory=StyledPilImage, embeded_image_path=STYLE_IMAGE_PATH)
    else:
        img = qr.make_image()

    orig_width = img.size[0]
    height = img.size[1]
    font = ImageFont.truetype("files/static/font.ttf", 40)
    answer = text
    text_len = font.getlength(answer)
    width = int(max(orig_width + 50, text_len + 50))
    offset = 25
    if text_len + 50 > orig_width:
        offset = int((text_len + 50 - orig_width)/2)
    with_text = Image.new(mode="RGB", size=(width, height + 50))
    draw = ImageDraw.Draw(with_text)
    draw.rectangle([(0, 0), with_text.size], fill=(255, 255, 255))
    draw.rectangle([(offset, 0), (offset + img.width, img.height)], fill=(255, 255, 255))
    with_text.paste(img, (offset, 0))
    draw.text((width/2-text_len/2, height - 30),
              answer, align="center", fill=(0, 0, 0), font=font)

    with_text.save(blob, "PNG")

    with open("qr_codes/qr-" + str(num) + ".png", "wb") as outfile:
        outfile.write(blob.getbuffer())
