'''

    modules.simul.main

    configuration = {
        "rope"
    }

'''

import math

from src.error import InvalidSetup

class Simulate:
    def __init__(self):
        self.v = []
        self.a = []
        self.s = []
        self.V = lambda v, a, t: v + a * t
        self.S = lambda s, v, a, t: s + v * t + 1/2 * a * t**2
    def __call__(self, conf):
        self.__main     = conf     # Properties regarding gravity and the lift itself.
        # calculate initial conditions.
        print("Calculating initial variables...")
        self.__calculate_physics_initial()
        print("Testing motor force capability...")
        self.__check_physics_motor_force(self.__lift_passenger_mass, True, +1, -1, -1, +1, -1, +1) 
        print(f"Motor force: Actual acceleration is {self.__t0_a_up} and {self.__t0_a_down}")
        print("Testing tension force capability...")
        self.__check_physics_tension_force(self.__lift_passenger_mass, True, +1, -1, -1, +1) 
        print(f"Cable force: Actual acceleration for T1 is {self.__t1_t1_a_up} and {self.__t1_t1_a_down}")
        print(f"Cable force: Actual acceleration for T2 is {self.__t1_t2_a_up} and {self.__t1_t2_a_down}")
        print("Testing pulley slip capability...")
        self.__check_physics_pulley_slip(self.__lift_passenger_mass, True, +1, -1, -1, +1)
        print(f"Cable slip: Actual acceleration is {self.__t2_a_up} and {self.__t2_a_down}")
        print("Finalizing boundary conditions...")
        self.__check_physics_set_boundaries()
    def __calculate_physics_initial(self):
        """Calculate the initial setup required."""
        # physical properties
        self.__step                 = self.__main["step"]                # time step between two data
        self.__gravity              = self.__main["gravity"]             # gravitational accel
        self.__acceleration         = self.__main["acceleration"]        # the current target accel, initial value is what we prefer
        self.__distance             = self.__main["distance"]            # distance per two floors
        # safety properties
        self.__max_motor_force      = self.__main["max_motor_force"]     # max motor force
        self.__max_cable_force      = self.__main["max_cable_force"]     # ultimate tensile strengh x cable area
        # discovered properties
        self.__t0_a_up              = 0                                  # Allowed edge accel for test 0 (testing motor)
        self.__t0_a_down            = 0                                  # Allowed edge accel for test 0 (testing motor)
        self.__t1_t1_a_up           = 0                                  # Allowed edge accel for test 1 (testing cable - t1, up)
        self.__t1_t1_a_down         = 0                                  # Allowed edge accel for test 1 (testing cable - t1, down)
        self.__t1_t2_a_up           = 0                                  # Allowed edge accel for test 1 (testing cable - t2, up)
        self.__t1_t2_a_down         = 0                                  # Allowed edge accel for test 1 (testing cable - t2, down)
        self.__t2_a_up              = 0                                  # Allowed edge accel for test 2 (testing slip - t1, up)
        self.__t2_a_down            = 0                                  # Allowed edge accel for test 2 (testing slip - t1, down)
        self.__actual_accel         = (0, 0)                             # The range of allowed acceleration.

        # mass properties
        self.__lift_mass            = self.__main["lift_mass"]           # lift mass
        self.__counterweight_mass   = self.__main["counterweight_mass"]  # counterweight mass
        self.__lift_passenger_mass  = self.__main["lift_passenger_mass"] # passenger's mass
        self.__pulley_rot_inertia   = self.__main["pulley_rot_inertia"]  # the rotational inertia of the pulley
        # friction property
        self.__pulley_friction      = self.__main["pulley_friction"]     # pulley friction force
        self.__lift_friction        = self.__main["lift_friction"] * ( # lift + passenger friction coef.
            self.__lift_mass + self.__lift_passenger_mass
        )
        self.__cw_friction          = self.__main["counterweight_friction"] * self.__counterweight_mass  
        self.__pulley_coefficient   = self.__main["pulley_coefficient"]  # pulley friction coef.
        # pulley property
        self.__radius               = self.__main["radius"]              # pulley radius 
        self.__wrap_angle           = self.__main["wrap_angle"]          # wrap angle of the cable, typically 180 degrees

        # Penalty for upper floors. if the counterweight is lighter, the lift wants to
        # go down naturally. Thus the penalty must be bigger. If the counterweight is heavier
        # aka the lift is empty or sparingly filled, the lift wants to go up naturally. Thus
        # the penalty must be smaller.
        self.__upper_penalty              = (self.__main["lift_passenger_mass"] + self.__main["lift_mass"]
                                       ) / self.__main["counterweight_mass"]
        self.__lower_penalty              = self.__main["counterweight_mass"] / (
                                        self.__main["lift_passenger_mass"] + self.__main["lift_mass"])
    def __check_physics_motor_force(self, passenger, up # indicates the direction
        # Get the origin and the sign of equation terms
        # these are sign modifiers, that are variables that can inject either -1 or +1
        # since we are using basic newtonian free body diagrams without specialized vector with same origin
        # we have to use this system.
            , t_1l # T1 for the lift
            , m_e  # mass of the lift + counterweight
            , t_2c # T2 for the counterweight
            , m_cw # mass of the counterweight
            , t_1p # T1 for the pulley
            , t_2p # T2 for the pulley
        ):
        """This function is used to test the lift under zero load."""
        if up:
            print("Checking motor force with condition up")
        else:
            print("Checking motor force with condition down")
        ###### calculate first
        # calculate the required force. you will see 1/t_1l and 1/t_2c,
        # this is because those two variables are attached like this
        # t_1l x T1 + ... = (mass lift + mass passengers) * a
        # t_2c x T2 + ... = (mass counterweight) * a
        # and when you define like this...
        # T1 = ...
        # T2 = ...
        # before plugging it to Sigma Torque = I x alpha
        # it will be defined as this
        # T1 = .......... / t_1l
        # T2 = .......... / t_2l
        # thus
        # T1 = force-1 / t_1l + force-2 / t_1l + ...
        # T2 = force-a / t_2c + force-2 / t_2c + ...
        ###### calculate whether the motor is capable during zero load event        
        F = (
            # gravity component
            (self.__lift_mass + passenger)        * self.__gravity * m_e  * t_1p * 1/t_1l
            + self.__counterweight_mass * self.__gravity * m_cw * t_2p * 1/t_2c
            # acceleration component
            - (self.__lift_mass + passenger)        * self.__acceleration * t_1p * 1/t_1l
            - self.__counterweight_mass * self.__acceleration * t_2p * 1/t_2c
            # friction component
            - self.__cw_friction     * t_2p * 1/t_2c
            - self.__lift_friction   * t_1p * 1/t_1l
            + self.__pulley_friction
            # inertia component
            + (self.__pulley_rot_inertia * self.__acceleration) / self.__radius ** 2
        )
        print(f"Motor force: F under preferred accel is {F} N")
        ###### if the force is more than what the motor can handle, abandon the preferred accel and try to calculate the a.
        if abs(F) > self.__max_motor_force:
            print("Motor force: F can't handle preferred accel")
            # can't keep up? we calculate the "supposed" accel by using the max motor force instead
            a = (
                - self.__max_motor_force
                + self.__pulley_friction
                + self.__lift_friction   * t_1p * 1/t_1l
                + self.__cw_friction     * t_2p * 1/t_2c
                + self.__gravity * (
                    + t_1p * m_e * 1/t_1l * (self.__lift_mass + passenger)
                    + t_2p * m_cw * 1/t_2c * self.__counterweight_mass
                )
            ) / (
                - self.__pulley_rot_inertia / self.__radius ** 2
                + t_1p * 1/t_1l * (self.__lift_mass + passenger)
                + t_2p * 1/t_2c * self.__counterweight_mass
            )
            if a <= 0: # this indicates the acceleration itself is negative or zero, indicating that the motor has given up
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up due to motor failure.")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down due to motor failure.")
            else: # if not, we will state that the preferred acceleration is impossible to achieve with max motor load requirement
                if up:
                    self.__t0_a_up = a
                else:
                    self.__t0_a_down = a
        else:
            if up:
                self.__t0_a_up = self.__acceleration
            else:
                self.__t0_a_down = self.__acceleration
        if up: # call it again recursively to test the opposite direction
            self.__check_physics_motor_force(passenger, False, -1, +1, +1, -1, +1, -1)
    def __check_physics_tension_force(self, passenger, up # default value you see here are for direction UP.
        # Get the origin and the sign of equation terms
        # these are sign modifiers, that are variables that can inject either -1 or +1
        # since we are using basic newtonian free body diagrams without specialized vector with same origin
        # we have to use this system.
            , t_1l # T1 for the lift
            , m_e  # mass of the lift + counterweight
            , t_2c # T2 for the counterweight
            , m_cw # mass of the counterweight
        ):
        """This is used to check the ability for the cable to hold up together."""
        if up:
            print("Checking cable force with condition up")
        else:
            print("Checking cable force with condition down")
        # we will get the equation for t2
        ###### check the UTS test
        print("Cable force: Checking T1")
        t1 = (
            + (self.__lift_mass + passenger) * self.__acceleration
            - (self.__lift_mass + passenger) * self.__gravity * m_e
            + self.__lift_friction
        ) *  1/t_1l
        print(f"Cable force: T1 is {t1} under preferred accel")
        if t1 > self.__max_cable_force: # if T1 > max allowed cable tension force, we force t1 = max cable tension force
            print("Cable force: T1 is incapable of preferred accel")
            a = (
                + self.__max_cable_force * t_1l
                - self.__lift_friction
                + (self.__lift_mass + passenger) * self.__gravity * m_e
            ) / (
                (self.__lift_mass + passenger)
            )
            if a <= 0:
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up due to cable T1 failure.")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down due to cable T1 failure.")
            else:
                if up:
                    self.__t1_t1_a_up = a
                else:
                    self.__t1_t1_a_down = a        
        else:
            if up:
                self.__t1_t1_a_up = self.__acceleration
            else:
                self.__t1_t1_a_down = self.__acceleration
        print("Cable force: Checking T2")
        t2 = (
            + self.__counterweight_mass * self.__acceleration
            - self.__counterweight_mass * self.__gravity * m_cw
            + self.__cw_friction
        ) *  1/t_2c
        print(f"Cable force: T2 is {t2} under preferred accel")
        if t2 > self.__max_cable_force: # if T2 > max allowed cable tension force, we force t1 = max cable tension force
            print("Cable force: T2 is incapable of preferred accel")
            a = (
                + self.__max_cable_force * t_1l
                - self.__lift_friction
                + (self.__lift_mass + passenger) * self.__gravity * m_e
            ) / (
                (self.__lift_mass + passenger)
            )
            if a <= 0:
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up due to cable T2 failure.")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down due to cable T2 failure.")
            else:
                if up:
                    self.__t1_t2_a_up = a
                else:
                    self.__t1_t2_a_down = a
        else:
            if up:
                    self.__t1_t2_a_up = self.__acceleration
            else:
                self.__t1_t2_a_down = self.__acceleration
        if up: # call it again recursively to test the opposite direction
            self.__check_physics_tension_force(passenger, False, -1, +1, +1, -1)
    def __check_physics_pulley_slip(self, passenger, up # default value you see here are for direction UP.
        # Get the origin and the sign of equation terms
        # these are sign modifiers, that are variables that can inject either -1 or +1
        # since we are using basic newtonian free body diagrams without specialized vector with same origin
        # we have to use this system.
            , t_1l # T1 for the lift
            , m_e  # mass of the lift + counterweight
            , t_2c # T2 for the counterweight
            , m_cw # mass of the counterweight
        ):
        """This is used to check the ability for the cable to hold up together."""
        if up:
            print("Checking cable slip with condition up")
        else:
            print("Checking cable slip with condition down")
        t1 = (
            + (self.__lift_mass + passenger) * self.__acceleration
            - (self.__lift_mass + passenger) * self.__gravity * m_e
            + self.__lift_friction
        ) *  1/t_1l
        t2 = (
            + self.__counterweight_mass * self.__acceleration
            - self.__counterweight_mass * self.__gravity * m_cw
            + self.__cw_friction
        ) *  1/t_2c
        if max(t1, t2) == t1:
            t_max = 1
            print(f"Cable slip: T_max is T{t_max}")
        else:
            t_max = 2
            print(f"Cable slip: T_max is T{t_max}")
        capstan = math.e ** (self.__pulley_coefficient * self.__wrap_angle)
        print(f"Cable slip: Capstan's value is {capstan}")
        print(f"Cable slip: Current ratio is {max(t1, t2)/min(t1, t2)}")
        if max(t1, t2)/min(t1, t2) > capstan:
            if t_max == 1:
                a = (
                    + (self.__lift_mass + passenger) * self.__gravity * m_e / t_1l
                    - self.__lift_friction / t_1l
                    - self.__counterweight_mass * self.__gravity * capstan / t_2c
                    + self.__cw_friction * capstan / t_2c
                ) / ((self.__lift_mass + passenger) / t_1l - self.__counterweight_mass * capstan / t_2c)
            else:
                a = (
                    + self.__counterweight_mass * self.__gravity * m_e / t_2c
                    - self.__cw_friction / t_2c
                    - (self.__lift_mass + passenger) * self.__gravity * capstan / t_1l
                    + self.__lift_friction * capstan / t_1l
                ) / (self.__counterweight_mass / t_2c - (self.__lift_mass + passenger) * capstan / t_1l)
            if a < 0:
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up due to slip failure.")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down due to slip failure.")
            else:
                if up:
                    self.__t2_a_up = a
                else:
                    self.__t2_a_down = a
        else:
            if up:
                self.__t2_a_up = self.__acceleration
            else:
                self.__t2_a_down = self.__acceleration         
        if up: # call it again recursively to test the opposite direction
            self.__check_physics_pulley_slip(passenger, False, -1, +1, +1, -1)
    def __check_physics_set_boundaries(self):
        if min(self.__t0_a_up, self.__t1_t1_a_up, self.__t2_a_up) < self.__t1_t2_a_up:
            raise InvalidSetup("Acceleration range is invalid when setting up up range.")
        else:
            up_range = (
                min(self.__t0_a_up, self.__t1_t1_a_up, self.__t2_a_up),
                self.__t1_t2_a_up
            )
            print(f"FINAL: Up range is {up_range}")
        if max(self.__t0_a_up, self.__t1_t2_a_up, self.__t2_a_up) > self.__t1_t1_a_up:
            raise InvalidSetup("Acceleration range is invalid when setting up down range..")
        else:
            down_range = (
                self.__t1_t1_a_down,
                max(self.__t0_a_down,self.__t1_t2_a_down, self.__t2_a_down)
            )
            print(f"FINAL: Down range is {down_range}")
        minimal = max(up_range[0], down_range[0])        
        maximal = min(up_range[1], down_range[1])  
        if minimal > maximal:
            raise InvalidSetup("Acceleration range is invalid when setting up general range.")
        self.__actual_accel = (
            minimal, maximal
        )
        print(f"FINAL RESULT: {self.__actual_accel}")
         
Simulate()({
    "step" : 0.5,
    "gravity" : 10,
    "acceleration"            : 0
    ,"distance"               : 10
    ,"max_motor_force"        : 600
    ,"max_cable_force"        : 1000
    ,"lift_mass"              : 50
    ,"lift_passenger_mass"    : 40.909075
    ,"counterweight_mass"     : 75
    ,"pulley_rot_inertia"     : 20
    ,"pulley_friction"        : 5
    ,"pulley_coefficient"     : 0.5
    ,"counterweight_friction" : 0
    ,"lift_friction"          : 0
    ,"radius"                 : 0.5
    ,"wrap_angle"             : math.pi

})