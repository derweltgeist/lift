import math
import random

from src.main.physics import Physics
from src.error import InvalidSetup

class Simulate:
    def __init__(self, conf):
        self.v = []
        self.a = 0
        self.s = []
        self.t = []
        self.V = lambda v, a, t: v + a * t
        self.S = lambda s, v, a, t: s + v * t + 1/2 * a * t**2
        self.__main = conf
        self.__lower_penalty = (self.__main["lift_passenger_mass"] + self.__main["lift_mass"]
                                       ) / self.__main["counterweight_mass"]
        self.__upper_penalty = self.__main["counterweight_mass"] / (
                                        self.__main["lift_passenger_mass"] + self.__main["lift_mass"])
        self.__physics = Physics(conf)
    def __call__(self, human):
        self.__distance = self.__main["distance"]
        self.__step     = self.__main["step"]
        self.__speed    = self.__main["speed"]
        self.__human    = human  # A dict, each floor is a int (key) and dict (value), the dict is:
                                 #  "mass"  : Total human mass delta            (float)
                                 #  "up"    : Go up?                            (bool)
                                 #  "down"  : Go down?                          (bool)
        # Max floor length.
        self.__floor_length  = len(self.__human.keys())
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
        # position of the lift
        self.__lift_pos  = self.__main["position"]
        # provide initial conditions.
        self.s.append(self.__lift_pos * self.__distance)
        self.v.append(0)
        self.add_time_series()
        # calculate initial directions
        self.__direction = self.__calculate_direc()
        # calculate initial conditions.
        self.__accel = self.__physics()
        # loop of the simulation
        generate_destination = True
        while True:
            print("[simulator.__call__] Initiating movement loop...")
            try:
                print(f"Previous position array: {self.s}")
                print(f"Previous speed array: {self.v}")
                # time to reach.
                if self.__direction:
                    print("[simulator.__call__] We are going up.")
                    self.__calculate_change(self.__top_request_floor[0])
                    self.__lift_pos = self.__top_request_floor[0]
                else:
                    print("[simulator.__call__] We are going down.")
                    self.__calculate_change(self.__bottom_request_floor[0])
                    self.__lift_pos = self.__bottom_request_floor[0]
                # cut the requested floor, because we have reached it.
                if self.__direction:
                    self.__top_request_floor    = self.__top_request_floor[1:]
                else:
                    self.__bottom_request_floor = self.__bottom_request_floor[1:]
                # if empty, that means we are done.
                if self.__top_request_floor == [] and self.__bottom_request_floor == []:
                    break
                if generate_destination:
                    self.__give_targets() # We only run once so that the simulation can end.
                    generate_destination = False
                # insert more dudes
                self.__main["lift_passenger_mass"] = self.__main["lift_passenger_mass"] + self.__human[self.__lift_pos]["mass"]
                self.__physics.run(self.__main)
                self.__accel = self.__physics()
                self.__direction: bool = self.__calculate_direc()
            except KeyboardInterrupt:
                print("Stopping simulation")
    def __give_targets(self):
        """Gives passengers destination."""
        # idea is that we will loop within the request floor
        # if there is a jump (e.g. from floor 2 to 4), we will randomly decide whether
        # floor 3 will be clicked as the destination.
        # we only do this once tho because if we don't do that the simulation will keep
        # running forever.
        if self.__direction:
            minimal = self.__lift_pos
            step = 0
            for i, floor in enumerate(self.__top_request_floor):
                if i == len(self.__top_request_floor) - 1:
                    step += 1
                supposed_floor = minimal + step
                if floor > supposed_floor: # a break
                    print("[simulator.__give_targets] A break is detected!")
                    delta = floor - supposed_floor
                    num = random.randint(0, delta)
                    destination_floor = self.__lift_pos + num
                    if destination_floor != self.__lift_pos: # if it is not the same, we insert it to the request.
                        print(f"[simulator.__give_targets] New destination floor is {destination_floor}!")
                        self.__top_request_floor.insert(i, destination_floor)
        else:
            try:
                minimal  = self.__bottom_request_floor[-1]
            except IndexError:
                return
            step = 0
            for i, floor in enumerate(self.__bottom_request_floor):
                if i == len(self.__bottom_request_floor) - 1:
                    step -= 1
                supposed_floor = minimal + step
                if floor < supposed_floor: # a break
                    delta = supposed_floor - floor
                    num = random.randint(0, delta)
                    destination_floor = self.__lift_pos - num
                    if destination_floor != self.__lift_pos: # if it is not the same, we insert it to the request.
                        self.__top_request_floor.insert(i, destination_floor)
    def add_time_series(self):
        try:
            self.t.append(self.t[-1] + self.__step)
        except IndexError:
            self.t.append(self.__step)

    def __calculate_change(self, request: int):
        """Calculate GLBB."""
        print(f"Posisi lift adalah {self.__lift_pos}")
        origin = self.__lift_pos * self.__distance
        target = request         * self.__distance
        if self.__direction:
            way = +1
            a_way = +1
        else:
            way = -1
            a_way = -1
        print(way)
        distance = abs(target - origin)
        s_min = self.__speed ** 2 / self.__accel
        s_acc = self.__speed ** 2 / (2 * self.__accel)
        first_time = True
        if distance > s_min:
            print("[simulator.__calculate_change] Trapezoid speed curve is selected.")
            # trapezoid
            while True:
                print("[simulator.__calculate_change] Trapezoid - Accelerating...")
                s = self.S(self.s[-1], self.v[-1], a_way * self.__accel, self.__step)
                v = way * self.V(self.v[-1], a_way * self.__accel, self.__step)
                self.s.append(s)
                self.v.append(v)
                self.add_time_series()
                if first_time:
                    first_time = False
                    way = +1
                if s >= (origin + s_acc) or s <= (origin - s_acc):
                    break
            while True:
                print("[simulator.__calculate_change] Trapezoid - Crusing...")
                s = self.s[-1] + self.v[-1] * self.__step
                v = self.v[-1]
                self.s.append(s)
                self.v.append(v)
                self.add_time_series()
                if s >= (origin + (distance - s_acc)) or s <= (origin - (distance - s_acc)):
                    break
            while True:
                print("[simulator.__calculate_change] Trapezoid - De-accelerating...")
                s = self.S(self.s[-1], self.v[-1], -1 * a_way * self.__accel, self.__step)
                v = self.V(self.v[-1], -1 * a_way * self.__accel, self.__step)
                self.s.append(s)
                self.v.append(v)
                self.add_time_series()
                if s >= (origin + distance) or s <= (origin - distance):
                    break
        else:
            print("[simulator.__calculate_change] Triangle speed curve is selected.")
            # triangle
            v_max = math.sqrt(self.__accel * distance)
            while True:
                print("[simulator.__calculate_change] Triangle - Accelerating...")
                s = self.S(self.s[-1], self.v[-1], a_way * self.__accel, self.__step)
                v = way * self.V(self.v[-1], a_way * self.__accel, self.__step)
                self.s.append(s)
                self.v.append(v)
                self.add_time_series()
                if first_time:
                    first_time = False
                    way = +1
                print(v)
                if v >= v_max or v <= - v_max:
                    break
            while True:
                print("[simulator.__calculate_change] Triangle - De-accelerating...")
                s = self.S(self.s[-1], self.v[-1], -1 * a_way * self.__accel, self.__step)
                v = self.V(self.v[-1], -1 * a_way * self.__accel, self.__step)
                self.s.append(s)
                self.v.append(v)
                self.add_time_series()
                if s >= (origin + distance) or s <= (origin - distance):
                    break
            
        print(f"[simulator.__calculate_change] Successfully moved to request {request}")
    def __calculate_direc(self) -> bool:
        """Calculate whether the lift should go up or down via scoring system."""
        self.__upper_scores  = 0
        self.__lower_scores  = 0
        alpha: int = 0
        beta:  int = 0
        # Begin looping to calculate floor score.
        for floor, data in self.__human.items():
            print(f"[simulator.__calculate_direc] Floor {floor}, up {data['up']}, down {data['down']}")
            if floor > self.__lift_pos: # Upper floors (the lift must go up)
                if data["up"] or data["down"]:
                    self.__request_floor[floor] = True
                    print(f"[simulator.__calculate_direc] Floor {floor}, request appended!")
                    self.__top_request_floor.append(floor)
                if data["up"]: # If someone press up
                    if floor < self.__top_floor_req: # free rider
                        print(f"[simulator.__calculate_direc] Floor {floor}, free rider detected!")
                        alpha = 0
                    else: # not free rider, +score for the delta between the current floor
                          # and the the highest floor.
                        print(f"[simulator.__calculate_direc] Floor {floor}, no-free-rider is detected!")
                        alpha = self.__floor_length - self.__lift_pos
                else:
                    alpha = 0
                if data["down"]: # If someone press down
                    print(f"[simulator.__calculate_direc] Floor {floor}, opposite-ist is detected!")
                    beta = floor * 2 - self.__lift_pos # +score for going up, then down to
                                                       # the worst case of the lowest floor
                else:
                    beta = 0
                print(f"[simulator.__calculate_direc] Floor {floor}, your alpha is {alpha}, your beta is {beta}!")
                self.__upper_scores += alpha + beta
            elif floor < self.__lift_pos: # Lower floors (the lift must go down)
                if data["up"] or data["down"]:
                    self.__request_floor[floor] = True
                    self.__bottom_request_floor.append(floor)
                    print(f"[simulator.__calculate_direc] Floor {floor}, request appended!")
                if data["up"]: # If someone press up
                    print(f"[simulator.__calculate_direc] Floor {floor}, opposite-ist is detected!")
                    #  must go down to the target floor, then to the highest floor (worst case)
                    alpha = self.__lift_pos + self.__floor_length - 2 * floor 
                else:
                    alpha = 0
                if data["down"]: # If someone press down
                    if floor > self.__bot_floor_req: # free rider
                        print(f"[simulator.__calculate_direc] Floor {floor}, free rider detected!")
                        beta = 0
                    else: # not free rider, assume worst case of wanting to go to the lowest floor.
                        print(f"[simulator.__calculate_direc] Floor {floor}, no-free-rider is detected!")
                        beta = self.__lift_pos
                else:
                    beta = 0
                print(f"[simulator.__calculate_direc] Floor {floor}, alpha {alpha}, beta {beta}")
                self.__lower_scores += alpha + beta
        print(f"[simulator.__calculate_direc] Upper penalty is {self.__upper_penalty}, lower penalty is {self.__lower_penalty}!")
        print(f"[simulator.__calculate_direc] Upper score is {self.__upper_scores}, lower score is {self.__lower_scores}!")
        print(
f"[simulator.__calculate_direc] Adjusted upper score is {self.__upper_scores * self.__upper_penalty}, adjusted lower score is {self.__lower_scores * self.__lower_penalty}!")
        if len(self.__bottom_request_floor) == 0:
            print(f"[simulator.__calculate_direc] One sided, lower request does not exist!")
            return True
        elif len(self.__top_request_floor) == 0:
            print(f"[simulator.__calculate_direc] One sided, higher request does not exist!")
            return False
        if self.__upper_scores * self.__upper_penalty < self.__lower_scores * self.__lower_penalty:
            print(f"[simulator.__calculate_direc] We are going up!")
            return True # indicates going up
        else:
            print(f"[simulator.__calculate_direc] We are going down!")
            self.__bottom_request_floor = list(reversed(self.__bottom_request_floor)) # reverse the order of insertion
            return False