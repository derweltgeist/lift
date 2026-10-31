'''

    modules.simul.main

    configuration = {
        "rope"
    }

'''

import math

from src.error import InvalidSetup

class Physics:
    def __init__(self, conf):
        self.v = []
        self.a = []
        self.s = []
        self.V = lambda v, a, t: v + a * t
        self.S = lambda s, v, a, t: s + v * t + 1/2 * a * t**2
        self.run(conf)
    def run(self, conf):
        self.__main = conf
    def __call__(self):
        # calculate initial conditions.
        self.calculate_physics_initial()
        self.check_physics_motor_force(self.__lift_passenger_mass, True, +1, -1, -1, +1, -1, +1) 
        self.check_physics_tension_force(self.__lift_passenger_mass, True, +1, -1, -1, +1) 
        self.check_physics_pulley_slip(self.__lift_passenger_mass, True, +1, -1, -1, +1)
        self.check_physics_set_boundaries()
        return self.__actual_accel
    def calculate_physics_initial(self):
        """Calculate the initial setup required."""
        # physical properties
        self.__gravity              = self.__main["gravity"]             # gravitational accel
        self.__acceleration         = self.__main["acceleration"]        # the current target accel, initial value is what we prefer
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
    def check_physics_motor_force(self, passenger, up # indicates the direction
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
        ###### if the force is more than what the motor can handle, abandon the preferred accel and try to calculate the a.
        if abs(F) > self.__max_motor_force:
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
            if a < 0: # this indicates the acceleration itself is negative or zero, indicating that the motor has given up
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up, thus it has failed")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down, thus it has failed")
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
            self.check_physics_motor_force(passenger, False, -1, +1, +1, -1, +1, -1)
    def check_physics_tension_force(self, passenger, up # default value you see here are for direction UP.
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
        # we will get the equation for t2
        ###### check the UTS test
        t1 = (
            + (self.__lift_mass + passenger) * self.__acceleration
            - (self.__lift_mass + passenger) * self.__gravity * m_e
            + self.__lift_friction
        ) *  1/t_1l
        if t1 > self.__max_cable_force: # if T1 > max allowed cable tension force, we force t1 = max cable tension force
            a = (
                + self.__max_cable_force * t_1l
                - self.__lift_friction
                + (self.__lift_mass + passenger) * self.__gravity * m_e
            ) / (
                (self.__lift_mass + passenger)
            )
            if a < 0:
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up, thus it has failed")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down, thus it has failed")
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
        t2 = (
            + self.__counterweight_mass * self.__acceleration
            - self.__counterweight_mass * self.__gravity * m_cw
            + self.__cw_friction
        ) *  1/t_2c
        if t2 > self.__max_cable_force: # if T2 > max allowed cable tension force, we force t1 = max cable tension force
            a = (
                + self.__max_cable_force * t_1l
                - self.__lift_friction
                + (self.__lift_mass + passenger) * self.__gravity * m_e
            ) / (
                (self.__lift_mass + passenger)
            )
            if a < 0:
                if up:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up, thus it has failed")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down, thus it has failed")
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
            self.check_physics_tension_force(passenger, False, -1, +1, +1, -1)
    def check_physics_pulley_slip(self, passenger, up # default value you see here are for direction UP.
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
        else:
            t_max = 2
        capstan = math.e ** (self.__pulley_coefficient * self.__wrap_angle)
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
                    raise InvalidSetup(f"Acceleration is negative during zero load and going up, thus it has failed")
                else:
                    raise InvalidSetup(f"Acceleration is negative during zero load and going down, thus it has failed")
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
            self.check_physics_pulley_slip(passenger, False, -1, +1, +1, -1)
    def check_physics_set_boundaries(self):
        """Compute the intersection of all inequalities"""
        # If the variable wants a to be as minimal as possible, it must be used as the upper bound.
        if min(self.__t0_a_up, self.__t1_t1_a_up, self.__t2_a_up) < self.__t1_t2_a_up:
            raise InvalidSetup("Acceleration range is invalid when setting up up range.")
        else:
            up_range = (
                min(self.__t0_a_up, self.__t1_t1_a_up, self.__t2_a_up),
                self.__t1_t2_a_up
            )
        # The opposite: Lower bound.
        if max(self.__t0_a_up, self.__t1_t2_a_up, self.__t2_a_up) > self.__t1_t1_a_up:
            raise InvalidSetup("Acceleration range is invalid when setting up down range..")
        else:
            down_range = (
                self.__t1_t1_a_down,
                max(self.__t0_a_down,self.__t1_t2_a_down, self.__t2_a_down)
            )
        minimal = max(up_range[0], down_range[0])        
        maximal = min(up_range[1], down_range[1])  
        if minimal > maximal:
            raise InvalidSetup("Acceleration range is invalid when setting up general range.")
        self.__actual_accel = (minimal + maximal) / 2 # take the median
