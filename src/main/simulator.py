import math

from src.main.physics import Physics
from src.error import InvalidSetup

class Simulate:
    def __init__(self, conf):
        self.v = []
        self.a = 0
        self.s = []
        self.V = lambda v, a, t: v + a * t
        self.S = lambda s, v, a, t: s + v * t + 1/2 * a * t**2
        self.__main = conf
        self.__upper_penalty = (self.__main["lift_passenger_mass"] + self.__main["lift_mass"]
                                       ) / self.__main["counterweight_mass"]
        self.__lower_penalty = self.__main["counterweight_mass"] / (
                                        self.__main["lift_passenger_mass"] + self.__main["lift_mass"])
        self.__physics = Physics(conf)
    def __call__(self, conf, human):
        self.__main     = conf     # Properties regarding gravity and the lift itself.
        self.__distance = conf["distance"]
        self.__step     = conf["step"]
        self.__speed    = conf["speed"]
        self.__human    = human  # A dict, each floor is a int (key) and dict (value), the dict is:
                                 #  "human" : How many humans                   (int)
                                 #  "mass"  : Total human mass delta            (float)
                                 #  "up"    : Go up?                            (bool)
                                 #  "down"  : Go down?                          (bool)
        # Max floor length.
        self.__floor_length  = len(self.__human.key()) - 1
        # Highest floor that sends a request.
        self.__top_floor_req = 0
        # Lowest floor that sends a request.
        self.__bot_floor_req = self.__floor_length
        # List of floors that state a request (either above/below or both)
        self.__request_floor        : dict = {}
        self.__top_request_floor    : list = []
        self.__bottom_request_floor : list = []
        # We must check the top-most floor that request anything.
        for floor, data in reversed(self.__human.items()):
            if data["up"] or data["down"]:
                self.__top_floor_req = floor
                break
        # We must check the bottom-most floor that request anything.
        for floor, data in self.__human.items():
            if data["up"] or data["down"]:
                self.__bot_floor_req = floor
                break
        # calculate initial conditions.
        self.__accel = self.__physics()
        # position of the lift
        self.__lift_pos  = self.__main["position"]
        # calculate initial directions
        self.__direction = self.__calculate_direc()
        # loop of the simulation
        while True:
            try:
                if self.__direction:
                    self.__calculate_change(self.__top_request_floor[0])
                else:
                    self.__calculate_change(self.__bottom_request_floor[0])
                self.__top_request_floor    = self.__top_request_floor[1:]
                self.__bottom_request_floor = self.__bottom_request_floor[1:]
                if self.__top_request_floor == [] or self.__bottom_request_floor == []:
                    break
                # insert more dudes
                self.__main["lift_passenger_mass"] = self.__main["lift_passenger_mass"] + self.__human[self.__lift_pos]["mass"]
                self.__physics.run(self.__main)
                self.__accel = self.__physics()
                self.__direction: bool = self.__calculate_direc()
            except KeyboardInterrupt:
                print("Stopping simulation")
    def __calculate_change(self, request: int):
        origin    = self.__lift_pos * self.__distance
        request   = request * self.__distance
        distance  = (request - self.__lift_pos) * self.__distance
        s_min = (self.__speed ** 2) / self.__accel
        if s_min <= distance:
            s_stop = self.__speed / (2 * self.__accel)
            prev_v = 0
            prev_s = origin
            while True:
                current_v = self.V(prev_v, self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                self.v.append(current_v)
                self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s
                if current_v >= self.__speed:
                    break
            while True:
                self.s.append(current_v * self.__step)
                if distance - sum(self.s) <= s_stop:
                    break
            while True:
                current_v = self.V(prev_v, -1 * self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, -1 * self.__accel, self.__step)
                self.v.append(current_v)
                self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s
                if current_s >= distance:
                    break          
        else:
            v_peak = math.sqrt(self.__accel * distance / 2)
            prev_v = 0
            prev_s = 0
            while True:
                current_v = self.V(prev_v, self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                self.v.append(current_v)
                self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s
                if current_v >= v_peak:
                    break
            while True:
                current_v = self.V(prev_v, -1 * self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, -1 * self.__accel, self.__step)
                self.v.append(current_v)
                self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s
                if current_s >= distance:
                    break     
        self.__lift_pos = request 
    def __calculate_direc(self) -> bool:
        """Calculate whether the lift should go up or down via scoring system."""
        self.__upper_scores  = 0
        self.__lower_scores  = 0
        alpha: int = 0
        beta:  int = 0
        # Begin looping to calculate floor score.
        for floor, data in self.__human.items():
            if floor > self.__lift_pos: # Upper floors (the lift must go up)
                if data["up"] or data["down"]:
                    self.__request_floor[floor] = True
                    self.__top_request_floor.append(floor)
                if data["up"]: # If someone press up
                    if floor < self.__top_floor_req: # free rider
                        alpha = 0
                    else: # not free rider, +score for the delta between the current floor
                          # and the the highest floor.
                        alpha = self.__floor_length - self.__lift_pos
                else:
                    alpha = 0
                if data["down"]: # If someone press down
                    beta = floor * 2 - self.__lift_pos # +score for going up, then down to
                                                       # the worst case of the lowest floor
                else:
                    beta = 0
                self.__upper_scores = alpha + beta
            elif floor < self.__lift_pos: # Lower floors (the lift must go down)
                if data["up"] or data["down"]:
                    self.__request_floor[floor] = True
                    self.__bottom_request_floor.append(floor)
                if data["up"]: # If someone press up
                    #  must go down to the target floor, then to the highest floor (worst case)
                    alpha = self.__lift_pos + self.__floor_length - 2 * floor 
                else:
                    alpha = 0
                if data["down"]: # If someone press down
                    if floor > self.__bot_floor_req: # free rider
                        beta = 0
                    else: # not free rider, assume worst case of wanting to go to the lowest floor.
                        beta = self.__lift_pos
                else:
                    beta = 0
                self.__lower_scores = alpha + beta
        if len(self.__bottom_request_floor) == 0:
            return True
        elif len(self.__top_request_floor) == 0:
            return False
        if self.__upper_scores * self.__upper_penalty < self.__lower_scores * self.__lower_penalty:
            return True # indicates going up
        else:
            self.__bottom_request_floor = list(reversed(self.__bottom_request_floor)) # reverse the order of insertion
            return False