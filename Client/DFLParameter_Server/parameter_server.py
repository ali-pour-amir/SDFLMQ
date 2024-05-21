import torch
import torch.nn as nn
from custom_models import VGG
from custom_datasets import CIFAR10
import json

from executable_class import PubSub_Base_Executable

class dflmq_parameter_server(PubSub_Base_Executable):
    
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
        self.cfg = {'VGG11': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
                    'VGG13': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
                    'VGG16': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
                    'VGG19': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M']}

        self.CoTPST = "Coo_to_PS_T"
        self.PSTCoT = "PS_to_Coo_T"
        self.PSTCliT = "PS_to_Cli_T"

        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        self.model_name = 'VGG19'
        self.global_model   =  VGG(self.model_name)
        self.dataset        = CIFAR10()

        self.client.subscribe(self.CoTPST)

    def _get_header_body(self , msg) -> list :
        header_body = str(msg.payload.decode()).split('::')
        print("MESSAGE Header: " + header_body[0])
        header_parts = header_body[0].split('|')
        return header_parts

    def _execute_on_msg(self,msg):
        header_parts = self._get_header_body(msg)

        if header_parts[2] == 'broadcast_model' : 
            self.broadcast_model()
            
    def execute_on_msg(self, client, userdata, msg) -> None :
        
        super().execute_on_msg(client, userdata, msg)
        self._execute_on_msg(msg)
        
    def broadcast_model(self):
        weights_and_biases = {}
        for name, param in self.global_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()

        model_params = json.dumps(weights_and_biases)
        self.publish(self.PSTCliT,"collect_logic_model"," -id all -model_name " + str(self.model_name)+ " -model_params " + model_params) 

