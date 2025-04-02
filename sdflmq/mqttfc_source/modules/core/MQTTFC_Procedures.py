import paho.mqtt.client as mqtt
import time as T
import os
class MQTTFC_Procedures:

    def __init__(self):
        self.wait_time = .5 # in sec
        self.registered_procedures = ['Topic_Naming_PUF_SinglePair']
    
    def parse_procedure_command(self,command, cmdline,fc_parser_func):
        if(command in self.registered_procedures):
            if(command == 'Topic_Naming_PUF_SinglePair'):

                id1 = cmdline.split(' -id1 ')[1].split(' -id2 ')[0]
                id2 = cmdline.split(' -id2 ')[1].split(';')[0]
                self.Topic_Naming_PUF_SinglePair(id1,id2,fc_parser_func)

    def Topic_Naming_PUF_SinglePair(self,id1,id2, parser_func):
        
        rep = 1000
        topic_sizes = [16,32,64,96,128,192]
        code_length = [1,2,3,4,5,6,7,8,9,10]
        
        # topic_sizes = [16]
        # code_length = [4]
        
        for ts in topic_sizes:
            for cl in code_length:
                for i in range(rep):
                    parser_func("run establish_private_topic -id1 " + str(id1) + " -id2 " + str(id2) + " -l " + str(ts) + " -rl " + str(cl))
                    T.sleep(self.wait_time)
                    parser_func("run wisper -id1 " + str(id1) + " -id2 " + str(id2))
                    T.sleep(self.wait_time)