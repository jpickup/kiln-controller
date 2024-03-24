import threading,logging,json,time,datetime
from oven import Oven, Profile
from displayhatmini import DisplayHATMini
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from ovenDisplayHandler import OvenDisplayHandler
from ovenEditDisplayHandler import OvenEditDisplayHandler
from ovenRunDisplayHandler import OvenRunDisplayHandler

log = logging.getLogger(__name__)

# display HAT setup
width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT
buffer = Image.new("RGB", (width, height))
displayhatmini = DisplayHATMini(buffer, backlight_pwm=True)
displayhatmini.set_led(0.0, 0.2, 0.0)
draw = ImageDraw.Draw(buffer)
# Font path on a Raspberry Pi running Raspbian
font_path = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
fnt15 = ImageFont.truetype(font_path, 15, encoding="unic")
fnt25 = ImageFont.truetype(font_path, 25, encoding="unic")
fnt50 = ImageFont.truetype(font_path, 50, encoding="unic")
fnt75 = ImageFont.truetype(font_path, 75, encoding="unic")
brightness = 1.0
instance = None
# GPIO pins
BUTTON_A = 5
BUTTON_B = 6
BUTTON_X = 16
BUTTON_Y = 24

def buttonA_callback(channel):
    if (not instance is None):
        instance.buttonA_clicked()

def buttonB_callback(channel):
    if (not instance is None):
        instance.buttonB_clicked()

def buttonX_callback(channel):
    if (not instance is None):
        instance.buttonX_clicked()

def buttonY_callback(channel):
    if (not instance is None):
        instance.buttonY_clicked()


class OvenDisplay(threading.Thread):
    def __init__(self,oven,ovenWatcher,sleepTime):
        instance = self
        self.lastCallback = datetime.datetime.now()
        GPIO.setmode(GPIO.BCM)
        GPIO.add_event_detect(BUTTON_A, GPIO.FALLING, callback=buttonA_callback, bouncetime=100)
        GPIO.add_event_detect(BUTTON_B, GPIO.FALLING, callback=buttonB_callback, bouncetime=100)
        GPIO.add_event_detect(BUTTON_X, GPIO.FALLING, callback=buttonX_callback, bouncetime=100)
        GPIO.add_event_detect(BUTTON_Y, GPIO.FALLING, callback=buttonY_callback, bouncetime=100)

        self.runDisplayHandler = OvenRunDisplayHandler(displayhatmini, draw, self)
        self.editDisplayHandler = OvenEditDisplayHandler(displayhatmini, draw, self)
        self.displayHandlers = [self.runDisplayHandler, self.editDisplayHandler]
        self.currentDisplayHandlerIdx = 0
        self.last_update = datetime.datetime.now()
        self.last_profile = None
        self.last_log = []
        self.started = None
        self.recording = False
        self.observers = []
        threading.Thread.__init__(self)
        self.display_lock = threading.Lock()
        self.daemon = True
        self.wakeup_display()
        # oven setup
        self.oven = oven
        self.ovenWatcher = ovenWatcher
        ovenWatcher.add_observer(self)
        self.sleep_time = sleepTime
        self.count = 0
        with self.display_lock:
            draw.rectangle((0, 0, width, height), (0, 0, 0))
            self.text("Initialising...", (25, 25), fnt25, (255,255,255))
            displayhatmini.display()
            displayhatmini.set_backlight(brightness)
            displayhatmini.set_led(0.0, 0.0, 0.0)
        self.start()

    def run(self):
        while True:
            timeSinceKeypress = datetime.datetime.now() - self.last_update
            # Only check if the button is still down if it wasn't pressed during the last cycle
            if (timeSinceKeypress.microseconds/1000000 + timeSinceKeypress.seconds) > self.sleep_time:
                a_pressed = displayhatmini.read_button(displayhatmini.BUTTON_A)
                b_pressed = displayhatmini.read_button(displayhatmini.BUTTON_B)
                x_pressed = displayhatmini.read_button(displayhatmini.BUTTON_X)
                y_pressed = displayhatmini.read_button(displayhatmini.BUTTON_Y)
                if (y_pressed):
                    self.nextDisplayHandler()
                if (x_pressed):
                    self.currentDisplayHandler().xPressed()
                if (a_pressed):
                    self.currentDisplayHandler().aPressed()
                if (b_pressed):
                    self.currentDisplayHandler().bPressed()
            with self.display_lock:
                self.currentDisplayHandler().render(self.oven.get_state())
            time.sleep(self.sleep_time)

    def buttonA_clicked(self):
        self.last_update = datetime.datetime.now()    
        self.currentDisplayHandler().aPressed()

    def buttonB_clicked(self):
        self.last_update = datetime.datetime.now()    
        self.currentDisplayHandler().bPressed()

    def buttonX_clicked(self):
        self.last_update = datetime.datetime.now()    
        self.currentDisplayHandler().xPressed()

    def buttonY_clicked(self):
        self.last_update = datetime.datetime.now()    
        self.nextDisplayHandler()

    def currentDisplayHandler(self):
        return self.displayHandlers[self.currentDisplayHandlerIdx]

    def nextDisplayHandler(self):
        self.currentDisplayHandlerIdx = (self.currentDisplayHandlerIdx+1) % len(self.displayHandlers)

    def update_profiles(self, new_profiles):
        log.info("New profiles ")
        log.info(new_profiles)
        for idx, dh in enumerate(self.displayHandlers):
            dh.update_profiles(new_profiles)

    def send(self,oven_state_json):
        oven_state = json.loads(oven_state_json)
        with self.display_lock:
            self.currentDisplayHandler().render(oven_state)

    def text(self, text, position, fnt, color):
        draw.text(position, text, font=fnt, fill=color)

    def wakeup_display(self):
        self.last_update = datetime.datetime.now()

    def runProfile(self, profile):
        log.info("Running profile: " + profile.name)
        # calculate the start time
        startAt = 0
        if ((not self.oven is None) and not self.oven.get_state() is None):
            ovenState = self.oven.get_state()
            currentTemp = ovenState['temperature']
            if (not currentTemp is None):
                startAt = profile.calc_start_offset(currentTemp)
                log.info("Shifted start to " + str(startAt))

        self.oven.run_profile(profile, startAt)
        self.showRunDisplay()

    def showRunDisplay(self):
        self.currentDisplayHandlerIdx = 0

    def abortRun(self):
        self.oven.abort_run()
