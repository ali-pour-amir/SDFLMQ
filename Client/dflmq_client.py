
from Global.executable_class import PubSub_Base_Executable
from Client_Classes.aggregator import dflmq_aggregator
from Client_Classes.trainer import dflmq_trainer
from Client_Classes.application_logic import dflmq_client_app_logic

import numpy as np
import psutil

class DFLMQ_Client(PubSub_Base_Executable) :
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
        self.client_logic   = dflmq_client_app_logic(id=self.id,
                                                     is_simulating=True)
        self.trainer        = dflmq_trainer()
        self.aggregator     = dflmq_aggregator()

        self.CoTClT = "Coo_to_Cli_T"
        self.CiTCoT = "Cli_to_Coo_T"
        self.PSTCoT = "PS_to_Cli_T"

        self.executables.extend(['echo_resources', 'fedAvg', 'client_update'])
        self.executables.extend(self.client_logic.executables)
        self.executables.extend(self.trainer.executables)
        self.executables.extend(self.aggregator.executables)
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        self.client.subscribe(self.CoTClT)
        self.client.subscribe(self.PSTCoT)
        
    # def _get_header_body(self , msg) -> list :
    #     header_body = str(msg.payload.decode()).split('::')
    #     print("MESSAGE Header: " + header_body[0])

    #     header_parts = header_body[0].split('|')
    #     return header_parts

    def _execute_on_msg  (self, header_parts, body): 
        if header_parts[2] == 'echo_resources' : 
            self.echo_resources()
            
    def execute_on_msg(self, header_parts, body) -> None :
        super().execute_on_msg(header_parts, body) 
        self._execute_on_msg(header_parts, body)
        
        self.client_logic._execute_on_msg(header_parts, body)
        self.trainer._execute_on_msg(header_parts, body)
        self.aggregator._execute_on_msg(header_parts, body)

    def echo_resources(self) -> None : 
        resources = {
            'cpu_count'     : psutil.cpu_count() ,
            'disk_usage'    : psutil.disk_usage("/") ,
            'cpu_frequency' : psutil.cpu_freq() ,
            'cpu_stats'     : psutil.cpu_stats() ,
            'net_stats'     : psutil.net_if_stats() ,
            'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
            'net_counters'  : psutil.net_io_counters()}

        res_msg = str(resources) # TODO : format the dictionary as string, later 
        self.publish(topic=self.controller_echo_topic,func_name="echo_resources",msg=res_msg)
        self.publish(topic=self.CiTCoT,func_name="parse_client_stats",msg=res_msg)


userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Client(myID = userID,
        broker_ip = 'localhost' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)
exec_program.base_loop()
