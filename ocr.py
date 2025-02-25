#External
from os import stat
from PIL import Image, ImageEnhance, ImageOps
import requests
import pytesseract as Tess
# Comment out this tesserocr import if changing stuff here when testing locally
import tesserocr
#Python
from functools import partial
import asyncio
#Internal
from utility import Utility

class OCR:
    bot = None
    local = None

    @classmethod
    def setup(cls, bot, local):
        cls.bot = bot
        cls.local = local

    @staticmethod
    async def detect_image_date(img_url):
        text, inverted_text = await asyncio.wait_for(OCR.detect_image_text(img_url), timeout = 60)
        try:
            text = text[100:]
            inverted_text = inverted_text[100:]
        except IndexError:
                text = text[50:]
                inverted_text = inverted_text[50:]
        img_date = Utility.date_from_txt(text) or Utility.date_from_txt(inverted_text)
        return img_date



    ### Tesseract text detection
    @classmethod
    async def detect_image_text(cls, img_url):
        # Uses Tesseract to detect text from url img 
        # return tuple of two possible text: normal and inverted

        # Set partial function for image_to_text
        if(cls.local):
            img_to_txt = partial(Tess.image_to_string, timeout=30)
        else:
            tess_path = r"/app/.apt/usr/share/tesseract-ocr/4.00/tessdata"
            img_to_txt = partial(tesserocr.image_to_text, path = tess_path)

        # Get image from url
        img_response = requests.get(img_url, stream=True)
        img_response.raw.decode_content = True
        img = Image.open(img_response.raw)
        img.load()

        # sharpen image
        enhancer = ImageEnhance.Sharpness(img)
        factor = 3
        img = enhancer.enhance(factor)

        # remove alpha channel and invert image
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) >= 4 else None) # 3 is the alpha channel
            img = background

        inverted_img = ImageOps.invert(img)

        # get text (run as coroutine to not block the event loop)
        text = await cls.bot.loop.run_in_executor(None, img_to_txt, img)

        # get inverted text (run as coroutine to not block the event loop)
        inverted_text = await cls.bot.loop.run_in_executor(None, img_to_txt, inverted_img)
        return (text, inverted_text)