import os
class Client:
    name = ""
    id = ""
    directory = ""
    broker = ""
    status = ""
    executables = [""]

    def __init__(self, name, id, type, directory, broker,executables=[]):
        self.name = name
        self.id = id
        self.type = type
        self.directory = directory
        self. broker = broker
        self.status = "OFF"
        self.executables = executables

    def power_on(self):
        return 0
    
    def power_off(self):
        return 0

    def check_status(self):
        return 0
    
    def update_status(self, new_status):
        self.status = new_status
    

