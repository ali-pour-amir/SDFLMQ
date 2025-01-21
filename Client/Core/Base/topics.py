
class MQTTFC_Base():
    def __init__(self):
        self.introduction_topic = "client_introduction"
        self.controller_executable_topic = "controller_executable"
        self.controller_echo_topic = "echo"


class SDFLMQ_(MQTTFC_Base):
    def __init__(self):
        super.__init__()
        self.CoTClT = "Coo_to_Cli_T"
        self.ClTCoT = "Cli_to_Coo_T"
        self.PSTCoT = "PS_to_Cli_T"
        self.PSTCliIDT = "PS_to_Cli_ID_"