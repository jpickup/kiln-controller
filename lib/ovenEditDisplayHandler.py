import logging
import json
from ovenDisplayHandler import OvenDisplayHandler
from oven import Oven, Profile

log = logging.getLogger(__name__)

class OvenEditDisplayHandler(OvenDisplayHandler):
    def __init__(self, displayhatmini, draw, ovenDisplay):
        super().__init__(displayhatmini, draw, ovenDisplay)
        self.fieldIdx = 0
        self.ramp = 90.0
        self.rampTarget = 750.0
        self.target = 1000.0
        self.soak = 10
        self.confirm = False
        self.maxRamp = 300
        self.ovenState = None

    def xPressed(self):
        self.fieldIdx += 1
        if (self.fieldIdx > 2):
            self.confirm = True
            self.fieldIdx = 0

    def aPressed(self):
        if (self.confirm):
            log.info("Confirmed")
            self.confirm = False
            self.run_profile()
        else:
            if (self.fieldIdx == 0):
                self.ramp += 10
            if (self.fieldIdx == 1):
                self.target += 10
            if (self.fieldIdx == 2):
                self.soak += 10

    def bPressed(self):
        if (self.confirm):
            log.info("Not confirmed")
            self.confirm = False
        else:
            if (self.fieldIdx == 0):
                self.ramp = max(self.ramp - 10, 0)
            if (self.fieldIdx == 1):
                self.target = max(self.target - 10, 0)
            if (self.fieldIdx == 2):
                self.soak = max(self.soak - 10, 0)

    def render(self, data):
        self.ovenState = data
        offset = 7
        titleHeight = 40
        grey = (192,192,192)
        white = (255,255,255)
        black = (0,0,0)
        red = (255,0,0)
        self.draw.rectangle((0, 0, self.width, self.height), black)

        self.setLedFromOvenState(data)

        if (self.confirm):
            self.text("Ramp: {0:2.0f}°C/h".format(self.ramp), (offset, offset), self.fnt25, white)
            self.text("Target: {0:2.0f}°C".format(self.target), (offset, offset + 25), self.fnt25, white)
            self.text("Soak: {0:2.0f}min".format(self.soak), (offset, offset + 50), self.fnt25, white)
            self.text("Confirm?", (offset, offset + 120), self.fnt35, red)
            self.text("▲ = Yes , ▼ = no", (offset, offset + 160), self.fnt35, grey)
        else:
            if (self.fieldIdx==0):
                title = "Ramp"
                value = "{0:2.0f}°C/h".format(self.ramp)
            elif (self.fieldIdx==1):
                title = "Target"
                value = "{0:2.0f}°C".format(self.target)
            elif (self.fieldIdx==2):
                title = "Soak"
                value = "{0:2.0f}min".format(self.soak)

            self.text(title, (offset, offset), self.fnt25, red)
            self.text(value, (offset, offset + titleHeight), self.fnt50, white)

        self.displayhatmini.display()
        self.displayhatmini.set_backlight(1.0)

    def run_profile(self):
        if (self.ovenState is None):
            log.warning("No oven state can't get current temp")
            currentTemp = 20
        else:    
            currentTemp = self.ovenState['temperature']

        name = "{0:2.0f}C {1:2.0f}C/h {2:2.0f}m soak".format(self.target, self.ramp, self.soak)
        p0 = [0, currentTemp]
        time1 = (self.rampTarget - currentTemp) * 3600 / self.ramp
        p1 = [time1, self.rampTarget]
        time2 = time1 + (self.target - self.rampTarget) * 3600 / self.maxRamp
        p2 = [time2, self.target]
        time3 = time2 + self.soak * 60
        p3 = [time3, self.target]
        data = [p0, p1, p2, p3]
        profileData = {
            'type': 'profile',
            'data': data,
            'name': name
        }
        jsonProfile = json.dumps(profileData)
        log.info(jsonProfile)
        profile = Profile(jsonProfile)
        self.ovenDisplay.runProfile(profile)
