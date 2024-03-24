import logging,json,datetime
from ovenDisplayHandler import OvenDisplayHandler
from oven import Oven, Profile

log = logging.getLogger(__name__)

class OvenRunDisplayHandler(OvenDisplayHandler):
    def __init__(self, displayhatmini, draw, ovenDisplay):
        super().__init__(displayhatmini, draw, ovenDisplay)
        self.count = 0
        self.profile = None
        self.dimmed = False

    def xPressed(self):
        if (not self.dimmed): 
            self.flip_oven_state()

    def aPressed(self):
        if (not self.dimmed): 
            self.prev_profile()

    def bPressed(self):
        if (not self.dimmed): 
            self.next_profile()

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
        log.info("Aborting run")
        self.ovenDisplay.abortRun()

    def start_oven(self):
        if (self.profile is None):
            log.error("No programme to start")
        else:
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

    # Example contents of oven_state
    # {'cost': 0, 'runtime': 0, 'temperature': 23.176953125, 'target': 0, 'state': 'IDLE', 'heat': 0, 'totaltime': 0, 'kwh_rate': 0.33631, 'currency_type': '£', 'profile': None, 'pidstats': {}}
    # {'cost': 0.003923616666666667, 'runtime': 0.003829, 'temperature': 23.24140625, 'target': 100.00079770833334, 'state': 'RUNNING', 'heat': 1.0, 'totaltime': 3600, 'kwh_rate': 0.33631, 'currency_type': '£', 'profile': 'test-200-250', 'pidstats': {'time': 1686902305.0, 'timeDelta': 5.027144, 'setpoint': 100.00079770833334, 'ispoint': 23.253125, 'err': 76.74767270833334, 'errDelta': 0, 'p': 1918.6918177083335, 'i': 0, 'd': 0, 'kp': 25, 'ki': 10, 'kd': 200, 'pid': 0, 'out': 1}}
    def render(self, data):
        self.oven_state = data
        time_since_last_keypress = datetime.datetime.now() - self.ovenDisplay.lastKeypress()
        self.dimmed = (time_since_last_keypress.total_seconds() > 120) and (self.oven_state['state'] != 'IDLE')        
        self.draw.rectangle((0, 0, self.width, self.height), (0, 0, 0))
        self.count += 1
        # TODO - remove this - will use up too much disk
        if (self.count % 40 == 0):
            log.info(self.oven_state)
        if (self.oven_state['temperature'] is not None):
            self.text("{0:2.0f}°C".format(self.oven_state['temperature']), (10, 10), self.fnt75, (255, 255, 255))
        else:
            self.text("---°C", (10, 10), self.fnt75, (255, 255, 255))

        if (self.oven_state['target'] is not None):
            self.text("Target: {0:2.0f}°C".format(self.oven_state['target']), (10, 90), self.fnt25, (255, 255, 255))
        else:
            self.text("Target: ---°C", (10, 90), self.fnt25, (255, 255, 255))

        if (self.oven_state['profile'] is not None):
            active_profile_name = self.oven_state['profile']
        else:
            if (self.profile is not None):
                active_profile_name = self.profile['name']
            else:
                active_profile_name = 'No Programme'

        self.text(active_profile_name, (10, 125), self.fnt25, (255, 0, 255))

        self.setLedFromOvenState(self.oven_state)

        if (self.oven_state['state'] is None):
            self.text("Initialising", (10, 10), self.fnt25, (255, 255, 255))
        else:
            self.text(self.oven_state['state'], (10, 160), self.fnt25, (255, 255, 255))
            if (self.oven_state['state'] != 'IDLE'):
                self.text(self.oven_state['state'], (10, 160), self.fnt25, (255, 255, 255))
                message = ''
                message_colour = (0,0,255)
                if (self.oven_state['totaltime'] is not None and self.oven_state['runtime'] is not None):
                    total_time = self.oven_state['totaltime']      
                    run_time = self.oven_state['runtime']  
                    time_left = total_time - run_time    
                    time_left_str = str(datetime.timedelta(seconds=round(time_left)))
                    message = 'Remaining: ' + time_left_str;
                if (self.oven_state['status'] is not None and self.oven_state['status'] != ""):
                    message = self.oven_state['status']
                    message_colour = (255,0,0)
                self.text(message, (10, 195), self.fnt25, message_colour)
        self.displayhatmini.display()
        self.displayhatmini.set_backlight(0.0 if self.dimmed else 1.0)
