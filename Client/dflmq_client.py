#This is legacy client
from Global.executable_class import PubSub_Base_Executable
from Client_Classes.aggregator import dflmq_aggregator
from Client_Classes.trainer import dflmq_trainer
from Client_Classes.application_logic import dflmq_client_app_logic
from Global import base_io
import numpy as np
import psutil
import json
import os
import tracemalloc

class DFLMQ_Client(PubSub_Base_Executable) :
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
        
        self.CoTClT = "Coo_to_Cli_T"
        self.ClTCoT = "Cli_to_Coo_T"
        self.PSTCoT = "PS_to_Cli_T"
        self.PSTCliIDT = "PS_to_Cli_ID_"
        os.system('setterm -background yellow -foreground black')
        os.system('clear')
        
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        self.client_logic   = dflmq_client_app_logic(id=self.id,
                                                     is_simulating=True,root_directory=self.root_directory)
        self.trainer        = dflmq_trainer()
        self.aggregator     = dflmq_aggregator()

        self.executables.extend(['echo_resources', 'client_update','fed_average','set_aggregator','send_local','receive_local','propagate_global', 'update_status'])
        self.executables.extend(self.client_logic.executables)
        self.executables.extend(self.trainer.executables)
        self.executables.extend(self.aggregator.executables)

        self.client.subscribe(self.CoTClT)
        self.client.subscribe(self.PSTCoT)
        self.client.subscribe(self.PSTCliIDT + self.id)
        
    # def _get_header_body(self , msg) -> list :
    #     header_body = str(msg.payload.decode()).split('::')
    #     print("MESSAGE Header: " + header_body[0])

    #     header_parts = header_body[0].split('|')
    #     return header_parts

    def _execute_on_msg  (self, header_parts, body): 
        # try:
            
            if header_parts[2] == 'echo_resources' : 
                model_name = body.split(' -model_name ')[1].split(' -dataset_name ')[0]
                dataset_name = body.split(' -dataset_name ')[1].split(';')[0]
                if((model_name == self.client_logic.logic_model_name) and (dataset_name == self.client_logic.simulated_logic_dataset_name)):
                    self.echo_resources()
                else:
                    print("Model name or Dataset name does not match!")
            if header_parts[2] == 'client_update' :
                if(self.trainer.is_trainer):
                    num_epochs = body.split(' -num_epochs ')[1].split(' -batch_size ')[0]
                    batch_size = body.split(' -batch_size ')[1].split(';')[0]

                    tracemalloc.start()
                    # tracemalloc.reset_peak()
                    updated_model = self.trainer.client_update( self.client_logic.simulated_logic_data_train,
                                                                self.client_logic.logic_model,
                                                                int(num_epochs),
                                                                int(batch_size),
                                                                round = 1)
                    
                    mem_usage = tracemalloc.get_traced_memory()[0]
                    tracemalloc.stop()

                    self.client_logic.logic_model = updated_model
                    print("Local model updated.")
                
                    
                    self.publish(self.ClTCoT,"local_training_complete" , " -id " + str(self.id) + " -mem " + str(mem_usage)) #ADD RAM USAGE
                
            if header_parts[2] == 'fed_average' :
                if(self.aggregator.is_aggregator):
                    
                    tracemalloc.start()
                    # tracemalloc.reset_peak()
                    self.client_logic.logic_model = self.aggregator.fed_average(self.client_logic.logic_model)
                    acc, loss = self.aggregator.agg_test(self.client_logic.logic_model,self.client_logic.simulated_logic_data_test)
                    mem_usage = tracemalloc.get_traced_memory()[0]
                    tracemalloc.stop()
                    self.publish(self.ClTCoT,"aggregation_complete"," -id " + self.id + " -model_acc " + str(acc) + " -model_loss " + str(loss) + " -mem " + str(mem_usage)) #ADD RAM USAGE

            if header_parts[2] == 'set_aggregator' : 
                id = body.split('-id ')[1].split(';')[0]
                self.set_aggregator(id)

            if header_parts[2] == 'send_local' : 
                id = body.split('-id ')[1].split(';')[0]
                if(self.trainer.is_trainer):
                    if(id == "all" or id == self.id):
                        if(self.aggregator.is_aggregator == False):       
                            self.send_local()
                        else:
                            print("No need to send locals, client is aggregator. Informing coordinator.")
                            self.publish(self.ClTCoT,"aggregator_received_local_params"," -id " + self.id)
                else:
                    print("can't send local model params because client is not a trainer!")

                    
            if header_parts[2] == 'receive_local' : 
                if(self.aggregator.is_aggregator):
                    id = body.split('-id ')[1].split(' -model_params ')[0]
                    model_params = body.split('-model_params ')[1].split(';')[0]
                    self.receive_local(id, model_params)
                else:
                    print("Receiving parameters, but not this client is not an aggregator.")

            if header_parts[2] == 'propagate_global' : 
               if(self.aggregator.is_aggregator == True):
                    self.propagate_global()

            if header_parts[2] == 'update_status' :
               ids = body.split('-ids ')[1].split(';')[0]
               ids = json.loads(ids)
               if(self.id in ids):
                    self.trainer.is_trainer = True
               else:
                    self.trainer.is_trainer = False

        # except:
        #     print("Something in the command message was not right! Try again.")

    def set_aggregator(self,id):
        if(id == self.id):
            self.aggregator.is_aggregator = True
            os.system('setterm -background blue -foreground white')
            os.system('clear')
            if(self.aggregator.current_agg_topic_r != "-1"):
                self.client.unsubscribe(self.aggregator.current_agg_topic_r)
            
            self.aggregator.current_agg_topic_r = "c2a_agg_"+id
            self.aggregator.current_agg_topic_s = "a2c_agg_"+id
            self.client.subscribe(self.aggregator.current_agg_topic_r)
        else:
            self.aggregator.is_aggregator = False
            os.system('setterm -background yellow -foreground black')
            os.system('clear')
            if(self.aggregator.current_agg_topic_r != "-1"):
                self.client.unsubscribe(self.aggregator.current_agg_topic_r)

            self.aggregator.current_agg_topic_s = "c2a_agg_"+id
            self.aggregator.current_agg_topic_r = "a2c_agg_"+id
            self.client.subscribe(self.aggregator.current_agg_topic_r)
                
            
        print("Aggregator topic: " + str(self.aggregator.is_aggregator))
   
    def receive_local(self,id, params):
        model_params = json.loads(params)
        self.aggregator.accumulate_params(model_params)
        print("Received and archived client " + id + " local model parameters.")
        self.publish(self.ClTCoT,"aggregator_received_local_params"," -id " + id)
    
    def send_local(self):
        weights_and_biases = {}
        if(self.trainer.is_trainer == False):
            return
        for name, param in self.client_logic.logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        # local_params = []
        # local_params.append({k: v.cpu() for k, v in self.client_logic.logic_model.state_dict().items()})
        model_params = json.dumps(weights_and_biases)
        print(len(model_params))
        self.publish(self.aggregator.current_agg_topic_s,"receive_local"," -id " + self.id + " -model_params " + str(model_params)) 
        print("Model parameters published to aggregator.")
    
    def propagate_global(self):
        weights_and_biases = {}
        for name, param in self.client_logic.logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()

        model_params = json.dumps(weights_and_biases)
        print(len(model_params))
        self.publish(self.aggregator.current_agg_topic_s,"collect_logic_model"," -id " + self.id + " -model_params " + str(model_params)) 
        print("Global model parameters published to clients. Informing Coordinator.")
        self.publish(self.ClTCoT,"global_model_propagated","")
    
    def execute_on_msg(self, header_parts, body) -> None :
        
        super().execute_on_msg(header_parts, body) 
        self._execute_on_msg(header_parts, body)
        
        self.client_logic.  _execute_on_msg(header_parts, body)
        self.trainer.       _execute_on_msg(header_parts, body)
        self.aggregator.    _execute_on_msg(header_parts, body)

    def echo_resources(self) -> None : 
        resources = {
            'cpu_count'     : psutil.cpu_count() ,
            # 'disk_usage'    : psutil.disk_usage("/") ,
            'cpu_frequency' : psutil.cpu_freq() ,
            # 'cpu_stats'     : psutil.cpu_stats() ,
            # 'net_stats'     : psutil.net_if_stats() ,
            'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
            # 'net_counters'  : psutil.net_io_counters()
            }

        res_msg = json.dumps(resources) # TODO : format the dictionary as string, later 
        # self.publish(topic=self.controller_echo_topic,func_name="echo_resources",msg=res_msg)
        self.publish(topic=self.ClTCoT,func_name="parse_client_stats",msg=res_msg)
        


userID = input("Enter UserID: ")
print("User with ID : " + userID +" is created.")

exec_program = DFLMQ_Client(myID = userID,
        broker_ip = 'localhost' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)
exec_program.base_loop()
