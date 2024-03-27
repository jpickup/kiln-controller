import logging,json,datetime
from ovenDisplayHandler import OvenDisplayHandler
from oven import Oven, Profile
import config

log = logging.getLogger(__name__)
grey = (192,192,192)
white = (255,255,255)
black = (0,0,0)
red = (255,0,0)
blue = (0,0,255)
magenta = (255, 0, 255)

class OvenRunDisplayHandler(OvenDisplayHandler):
    def __init__(self, displayhatmini, draw, ovenDisplay):
        super().__init__(displayhatmini, draw, ovenDisplay)
        self.count = 0
        self.profile = None
        self.dimmed = False
        self.confirmation = None

    def xPressed(self):
        if (not self.dimmed): 
            self.flip_oven_state()

    def aPressed(self):
        if (not self.dimmed): 
            if (self.confirmation is None):
                self.prev_profile()
            else:
                self.confirmed()
        else:
            log.info("waking up display")

    def bPressed(self):
        if (not self.dimmed): 
            if (self.confirmation is None):
                self.next_profile()
            else:
                self.not_confirmed()
        else:
            log.info("waking up display")

    def confirm(self, message, action):
        log.info("Confirming " + message)
        self.confirmation = {
            'message': message,
            'action': action,
            'time': datetime.datetime.now()
        }
        self.rerender()

    def confirmed(self):
        log.info("Confirmed " + self.confirmation['message'])
        action = self.confirmation['action']
        self.confirmation = None
        action()
        self.rerender()

    def not_confirmed(self):
        log.info("Not confirmed " + self.confirmation['message'])
        self.confirmation = None
        self.rerender()

    def flip_oven_state(self):
        # only act if we have state
        if (self.oven_state['state'] is not None):
            if (self.oven_state['state'] == 'IDLE'):
                self.start_oven()
            else:
                self.stop_oven()
        else:
            log.info("No state, can't flip oven")

    def stop_oven(self):
        self.confirm("Stop programme", self.do_stop_oven)

    def do_stop_oven(self):
        log.info("Aborting run")
        self.ovenDisplay.abortRun()

    def start_oven(self):
        if (self.profile is None):
            log.error("No programme to start")
        else:
            self.confirm("Start:\n" + self.profile['name'], self.do_start_oven)

    def do_start_oven(self):
        log.info("Starting run " + self.profile['name'])
        profile_json = json.dumps(self.profile)
        oven_profile = Profile(profile_json)
        self.ovenDisplay.runProfile(oven_profile)

    def prev_profile(self):
        log.info("Prev profile")
        idx = self.find_profile_idx()
        new_idx = (idx - 1) % len(self.profiles)
        self.profile = self.profiles[new_idx]

    def next_profile(self):
        log.info("Next profile")
        idx = self.find_profile_idx()
        new_idx = (idx + 1) % len(self.profiles)
        self.profile = self.profiles[new_idx]

    def find_profile_idx(self):
        for idx, p in enumerate(self.profiles):
            if (p == self.profile):
                return idx
        return 0

    def rerender(self):
        self.ovenDisplay.render()

    def render(self, data):
        time_since_last_keypress = datetime.datetime.now() - self.ovenDisplay.lastKeypress()
        self.dimmed = (time_since_last_keypress.total_seconds() > config.display_timeout) and (self.oven_state['state'] == 'IDLE')        
        self.oven_state = data
        if (self.confirmation is None):
            self.render_ovenstate()
        else:
            self.render_confirmation()
        self.displayhatmini.display()
        self.displayhatmini.set_backlight(0.0 if self.dimmed else 1.0)
        
    def render_confirmation(self):
        time_since_confirmation = datetime.datetime.now() - self.confirmation['time']
        if (time_since_confirmation.total_seconds() > config.confirmation_timeout):
            log.info("Timed-out waiting for confirmation")
            self.confirmation = None
        else:
            offset = 7
            self.draw.rectangle((0, 0, self.width, self.height), black)
            self.text(self.confirmation['message'], (offset, offset + 30), self.fnt35, white)
            self.text("Confirm?", (offset, offset + 150), self.fnt35, red)
            self.text("▲ = Yes , ▼ = no", (offset, offset + 180), self.fnt35, grey)
        
    # Example contents of oven_state
    # {'cost': 0, 'runtime': 0, 'temperature': 23.176953125, 'target': 0, 'state': 'IDLE', 'heat': 0, 'totaltime': 0, 'kwh_rate': 0.33631, 'currency_type': '£', 'profile': None, 'pidstats': {}}
    # {'cost': 0.003923616666666667, 'runtime': 0.003829, 'temperature': 23.24140625, 'target': 100.00079770833334, 'state': 'RUNNING', 'heat': 1.0, 'totaltime': 3600, 'kwh_rate': 0.33631, 'currency_type': '£', 'profile': 'test-200-250', 'pidstats': {'time': 1686902305.0, 'timeDelta': 5.027144, 'setpoint': 100.00079770833334, 'ispoint': 23.253125, 'err': 76.74767270833334, 'errDelta': 0, 'p': 1918.6918177083335, 'i': 0, 'd': 0, 'kp': 25, 'ki': 10, 'kd': 200, 'pid': 0, 'out': 1}}
    def render_ovenstate(self):    
        self.draw.rectangle((0, 0, self.width, self.height), black)
        self.count += 1
        # TODO - remove this - will use up too much disk
        if (self.count % 40 == 0):
            log.info(self.oven_state)
        if (self.oven_state['temperature'] is not None):
            self.text("{0:2.0f}°C".format(self.oven_state['temperature']), (10, 10), self.fnt75, white)
        else:
            self.text("---°C", (10, 10), self.fnt75, white)

        if (self.oven_state['target'] is not None):
            self.text("Target: {0:2.0f}°C".format(self.oven_state['target']), (10, 90), self.fnt25, white)
        else:
            self.text("Target: ---°C", (10, 90), self.fnt25, white)

        if (self.oven_state['profile'] is not None):
            active_profile_name = self.oven_state['profile']
        else:
            if (self.profile is not None):
                active_profile_name = self.profile['name']
            else:
                active_profile_name = 'No Programme'

        self.text(active_profile_name, (10, 125), self.fnt25, magenta)

        self.setLedFromOvenState(self.oven_state)

        if (self.oven_state['state'] is None):
            self.text("Initialising", (10, 10), self.fnt25, white)
        else:
            self.text(self.oven_state['state'], (10, 160), self.fnt25, white)
            if (self.oven_state['state'] != 'IDLE'):
                self.text(self.oven_state['state'], (10, 160), self.fnt25, white)
                message = ''
                message_colour = blue
                if (self.oven_state['totaltime'] is not None and self.oven_state['runtime'] is not None):
                    total_time = self.oven_state['totaltime']      
                    run_time = self.oven_state['runtime']  
                    time_left = total_time - run_time    
                    time_left_str = str(datetime.timedelta(seconds=round(time_left)))
                    message = 'Remaining: ' + time_left_str
                if (self.oven_state['status'] is not None and self.oven_state['status'] != ""):
                    message = self.oven_state['status']
                    message_colour = red
                self.text(message, (10, 195), self.fnt25, message_colour)
