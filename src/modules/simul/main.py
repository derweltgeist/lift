'''

    modules.simul.main

    configuration = {
        "rope"
    }

'''

class Simulate:
    def __init__(self, conf):
        self.__cable    = conf.cable    # Properties regarding the cable.
        self.__governor = conf.governor # Properties regarding the governor.
        self.__main     = conf.main     # Properties regarding the main things.
