import logging,datetime
from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

# base class for display handlers.
class OvenDisplayHandler:
    def __init__(self, displayhatmini, draw, ovenDisplay):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.displayhatmini = displayhatmini
        self.draw = draw
        self.ovenDisplay = ovenDisplay
        # Font path on a Raspberry Pi running Raspbian
        font_path = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        self.fnt15 = ImageFont.truetype(font_path, 15, encoding="unic")
        self.fnt20 = ImageFont.truetype(font_path, 20, encoding="unic")
        self.fnt25 = ImageFont.truetype(font_path, 25, encoding="unic")
        self.fnt35 = ImageFont.truetype(font_path, 35, encoding="unic")
        self.fnt50 = ImageFont.truetype(font_path, 50, encoding="unic")
        self.fnt75 = ImageFont.truetype(font_path, 75, encoding="unic")
        self.last_update = datetime.datetime.now()
        self.profiles = None

    def setLed(self, r, g, b):
        self.displayhatmini.set_led(r, g, b)

    def text(self, text, position, fnt, color):
        self.draw.text(position, text, font=fnt, fill=color)

    # 'Abstract' methods that sub-classes should implement
    def xPressed(self):
        pass

    def aPressed(self):
        pass

    def bPressed(self):
        pass

    def render(self, data):
        pass

    def wakeup_display(self):
        self.last_update = datetime.datetime.now()

    def update_profiles(self, new_profiles):
        self.profiles = new_profiles

    def setLedFromOvenState(self, oven_state):
        if ((oven_state['state'] is None) or (oven_state['state'] == 'IDLE')):
            self.setLed(0.0, 0.0, 0.0)        
        elif (oven_state['heat'] == 1.0):
            # red light indicates heating
            self.setLed(1.0, 0.0, 0.0)
        else:
            # blue light indicates coooling
            self.setLed(0.0, 0.0, 1.0)

