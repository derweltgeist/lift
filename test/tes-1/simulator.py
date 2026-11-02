import math
import random
from physics import Physics
from error import InvalidSetup

class Simulate:
    def __init__(self, conf):
        self.v = []
        self.a = 0
        self.s = []
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
            minimal  = self.__bottom_request_floor[-1]
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
    def __calculate_change(self, request: int):
        """Calculate floor change."""
        origin    = self.__lift_pos * self.__distance
        request   = request * self.__distance
        distance  = (request - self.__lift_pos) * self.__distance
        try:
            s_min = (self.__speed ** 2) / self.__accel
            print(f"[simulator.__calculate_change] s_min = {s_min}, distance = {distance}")
        except ZeroDivisionError:
            raise InvalidSetup("Acceleration can't be zero.")
        s_stop = self.__speed ** 2 / (2 * self.__accel) # total distance when deaccel or total distance when accel
        if s_min <= distance:
            print("[simulator.__calculate_change] Trapezoid speed curve is chosen!")
            prev_v = 0
            prev_s = origin
            # accel
            while True:
                print("[simulator.__calculate_change] Accelerating...")
                current_v = self.V(prev_v, self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                print(f"[simulator.__calculate_change] V = {self.__direction * current_v} m/s^2, S = {origin + self.__direction * current_s} m")
                if current_v >= self.__speed: # if apparently the current_v is higher than the max speed, we break.
                    # why? because that means we have reached cruising altitude.
                    self.v.append(self.__direction * current_v)
                    self.s.append(origin + self.__direction * s_stop)  
                    prev_v = current_v
                    prev_s = current_s
                    break  
                else:           
                    self.v.append(self.__direction * current_v)
                    self.s.append(origin + self.__direction * current_s)
                    prev_v = current_v
                    prev_s = current_s
            # constant v
            while True:
                print("[simulator.__calculate_change] Cruising...")
                self.v.append(self.__direction * self.__speed)
                current_s = prev_s + current_v * self.__step
                if current_s >= (distance - s_stop):
                    print(
    f"[simulator.__calculate_change] V = {self.__direction * self.__speed} m/s^2, S = {origin + self.__direction * (distance - s_stop)} m, distance {distance}, accel {self.__accel}")
                    self.s.append(origin + self.__direction * (distance - s_stop))
                    prev_s = distance - s_stop
                    break
                else:
                    print(f"[simulator.__calculate_change] V = {self.__direction * self.__speed} m/s^2, S = {origin + self.__direction * current_s} m, distance {distance}, accel {self.__accel}")
                    self.s.append(origin + self.__direction *current_s)
                    prev_s = current_s
            # deaccel
            while True:
                print("[simulator.__calculate_direc] Deaccelerating...")
                current_v = self.V(prev_v, -1 * self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                if current_v <= 0: # if apparently the current_v is smaller than zero, we break.
                    # why? because that means we have reached zero.
                    print(f"[simulator.__calculate_change] V = {0} m/s^2, S = {request} m")
                    self.v.append(0)
                    self.s.append(request) 
                    prev_v = 0
                    prev_s = request
                    break  
                else:            
                    print(f"[simulator.__calculate_change] V = {self.__direction * current_v} m/s^2, S = {origin + self.__direction * current_s} m")
                    self.v.append(self.__direction * current_v)
                    self.s.append(origin + self.__direction * current_s)
                    prev_v = current_v
                    prev_s = current_s         
        else:
            print("[simulator.__calculate_change] Triangular speed curve is chosen!")
            v_peak = math.sqrt(self.__accel * distance / 2)
            print(f"[simulator.__calculate_change] Peak speed = {v_peak}")
            prev_v = 0
            prev_s = 0
            # accel
            while True:
                print("[simulator.__calculate_change] Accelerating...")
                current_v = self.V(prev_v, self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                print(f"[simulator.__calculate_change] V = {current_v} m/s^2, S = {current_s} m")
                if current_v >= v_peak: # if apparently the current_v is higher than the max speed, we break.
                    # why? because that means we have reached cruising altitude.
                    self.v.append(current_v)
                    self.s.append(s_stop)  
                    break  
                else:           
                    self.v.append(current_v)
                    self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s
            # deaccel
            while True:
                print("Deaccelerating...")
                current_v = self.V(prev_v, -1 * self.__accel, self.__step)
                current_s = self.S(prev_s, prev_v, self.__accel, self.__step)
                if current_v <= 0: # if apparently the current_v is smaller than zero, we break.
                    # why? because that means we have reached zero.
                    print(f"[simulator.__calculate_change] V = {current_v} m/s^2, S = {request} m")
                    self.v.append(current_v)
                    self.s.append(request)  
                    break  
                else:            
                    print(f"[simulator.__calculate_change] V = {current_v} m/s^2, S = {current_s} m")
                    self.v.append(current_v)
                    self.s.append(current_s)
                prev_v = current_v
                prev_s = current_s        
        print(f"[simulator.__calculate_change] Position array: {self.s}")
        print(f"[simulator.__calculate_change] Speed array: {self.v}")
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

Simulate({
    "step"                    : 0.5
    ,"position"               : 3
    ,"speed"                  : 3
    ,"gravity"                : 10
    ,"acceleration"           : 1
    ,"distance"               : 5
    ,"max_motor_force"        : 1500
    ,"max_cable_force"        : 8000
    ,"lift_mass"              : 300
    ,"lift_passenger_mass"    : 200
    ,"counterweight_mass"     : 400
    ,"pulley_rot_inertia"     : 10
    ,"pulley_friction"        : 2
    ,"pulley_coefficient"     : 0.5
    ,"counterweight_friction" : 1
    ,"lift_friction"          : 1
    ,"radius"                 : 0.5
    ,"wrap_angle"             : math.pi

})({
    1 : {
        "up"   : True,
        "down" : False,
        "mass" : 50
    },
    2 : {
        "up"   : True,
        "down" : True,
        "mass" : 25
    },
    3 : {
        "up"   : False,
        "down" : False,
        "mass" : 60
    },
    4 : {
        "up"   : True,
        "down" : False,
        "mass" : 30
    },
    5 : {
        "up"   : True,
        "down" : False,
        "mass" : 76
    },
    6 : {
        "up"   : False,
        "down" : True,
        "mass" : 80
    }
})
