import json
import torch
import torch.nn as nn
# from Global.custom_models import VGG, MNISTMLP
# from Global.custom_datasets import CIFAR10, MNIST
from Base.executable_class import PubSub_Base_Executable
from io import BytesIO
import zlib

import base64

class dflmq_parameter_server(PubSub_Base_Executable):
    
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
       
        self.CoTPST = "Coo_to_PS_T"
        self.PSTCoT = "PS_to_Coo_T"
        self.PSTCliT = "PS_to_Cli_T"
        self.PSTCliIDT = "PS_to_Cli_ID_"
        self.executables.append('broadcast_model')
        self.executables.append('publish_dataset')
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        # self.model_stash   =   {'MNISTMLP' : MNISTMLP(),
        #                         'VGG11' : VGG('VGG11'),
        #                         'VGG3' : VGG('VGG3')}
        # self.dataset_stash        =   {'MNIST' : MNIST(),
        #                                'CIFAR10' : CIFAR10()}

        self.client.subscribe(self.CoTPST)

    def __execute_on_msg(self,header_parts, body):
        super().__execute_on_msg(header_parts, body)
        # header_parts = self._get_header_body(msg)
        if header_parts[2] == 'broadcast_model' :
            model_name = body.split('-model_name ')[1].split(';')[0]
            self.broadcast_model(model_name)
            
        if header_parts[2] == 'publish_dataset':
            dataset_name = body.split('-dataset_name ')[1].split(' -num_clients ')[0]
            num_clients = int(body.split('-num_clients ')[1].split(' -ids ')[0])
            ids = (body.split(' -ids ')[1].split(';')[0]).split(' ')
            if(num_clients != len(ids)):
                print("number of clients does not match with number of ids passed.")
            else:
                self.publish_dataset(num_clients, dataset_name, ids)
      
    def broadcast_model(self,model_name):
        model = self.model_stash[model_name]
        weights_and_biases = {}
        for name, param in model.named_parameters():
            weights_and_biases[name] = param.data.tolist()

        model_params = json.dumps(weights_and_biases)
        print(len(model_params))
        self.publish(self.PSTCliT,"construct_logic_model"," -id all -model_name " + model_name + " -model_params " + str(model_params)) 
        
    def publish_dataset(self, num_clients, dataset_name, client_ids):
        
        [traindata_splits, testdata] = self.dataset_stash[dataset_name].load_data_for_clients(num_clients)
        for i in range(num_clients):
            print("buffering training dataset for client " + str(client_ids[i]))
            buffer = BytesIO()
            torch.save({'trainset': traindata_splits[i], 'testset': testdata}, buffer)
            buffer.seek(0)  # Rewind the buffer to the beginning
            
            #bin_dataset = buffer.read()
            #bin_datasets = f'{buffer.read()}'
            compressed_data = zlib.compress(buffer.read())
            compressed_data_s = base64.b64encode(compressed_data).decode('utf-8')

            self.publish(self.PSTCliIDT + client_ids[i],"collect_logic_data"," -id " + client_ids[i] + " -dataset_name " + dataset_name + " -dataset_type " + "training,testing"  + " -data " + compressed_data_s) 
            buffer.close()


# userID = input("Parameter Server ID: ")
# print("PS with ID=" + userID +" is created.")

# exec_program = dflmq_parameter_server(myID = userID,
#         broker_ip = 'localhost' ,
#         broker_port = 1883,
#         introduction_topic='client_introduction',
#         controller_executable_topic='controller_executable',
#         controller_echo_topic="echo",
#         start_loop=False
# )
# exec_program.base_loop()

