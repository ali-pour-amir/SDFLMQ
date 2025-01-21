
from Base.executable_class import PubSub_Base_Executable
from Modules.Client_Modules.aggregator import SDFLMQ_Aggregator
from Modules.Client_Modules.role_arbiter import Role_Arbiter
from Modules.model_controller import Model_Controller

from Base.topics import SDFLMQ_

# from Modules.model_controller import ...
# from Modules.role_arbiter import ...

from Base import base_io
import numpy as np
import psutil
import json
import os
import tracemalloc

class SDFLMQ_Client(PubSub_Base_Executable) :
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
        topics = SDFLMQ_()
        self.CoTClT = topics.CoTClT
        self.ClTCoT = topics.ClTCoT
        self.PSTCoT = topics.PSTCoT
        self.PSTCliIDT = topics.PSTCliIDT

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
        
        self.aggregator     = SDFLMQ_Aggregator()
        self.arbiter        = Role_Arbiter()
        self.controller     = Model_Controller()

        self.executables.extend(['echo_resources', 
                                 'client_update',
                                 'fed_average',
                                 'set_aggregator',
                                 'send_local',
                                 'receive_local',
                                 'propagate_global',
                                 'update_status'])
    
        self.executables.extend(self.aggregator.executables)
        self.client.subscribe(self.CoTClT)
        self.client.subscribe(self.PSTCoT)
        self.client.subscribe(self.PSTCliIDT + self.id)



    def _execute_on_msg  (self, header_parts, body): 
        # try:
            
            if header_parts[2] == 'echo_resources' :
                session_id = body.split(' -session_id ')[1].split(';')[0]
                if(session_id == self.session_id):
                    self.echo_resources()
                else:
                    print("session id does not match!")

            if header_parts[2] == 'fed_average' :##TODO: Put this in the aggregator pipeline script
                if(self.aggregator.is_aggregator):
                    
                    tracemalloc.start()
                    # tracemalloc.reset_peak()
                    self.client_logic.logic_model = self.aggregator.fed_average(self.client_logic.logic_model)
                    acc, loss = self.aggregator.agg_test(self.client_logic.logic_model,self.client_logic.simulated_logic_data_test)
                    mem_usage = tracemalloc.get_traced_memory()[0]
                    tracemalloc.stop()
                    self.publish(self.ClTCoT,"aggregation_complete"," -id " + self.id + " -model_acc " + str(acc) + " -model_loss " + str(loss) + " -mem " + str(mem_usage)) #ADD RAM USAGE

            if header_parts[2] == 'set_aggregator' : ##TODO: Put this in the aggregator pipeline script
                id = body.split('-id ')[1].split(';')[0]
                self.set_aggregator(id)

         
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

            if header_parts[2] == 'update_status' : ##TODO: associate this to Role_Arbiter
               ids = body.split('-ids ')[1].split(';')[0]
               ids = json.loads(ids)
               if(self.id in ids):
                    self.trainer.is_trainer = True
               else:
                    self.trainer.is_trainer = False

        # except:
        #     print("Something in the command message was not right! Try again.")

    def set_aggregator(self,id): #TODO: Move this to the Role Arbiter module
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
    
    def send_local(self,logic_model):
        weights_and_biases = {}
        for name, param in logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        model_params = json.dumps(weights_and_biases)
        self.publish(self.aggregator.current_agg_topic_s,"receive_local"," -id " + self.id + " -model_params " + str(model_params))
        print("Model parameters published to aggregator.")
    
    def propagate_global(self): #TODO: Move this to Parameter Server Logic
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
        self.aggregator.    _execute_on_msg(header_parts, body)

    def echo_resources(self,res_msg) -> None : 
        self.publish(topic=self.ClTCoT,func_name="parse_client_stats",msg=res_msg)
    
    def create_fl_session(self, 
                            session_id,
                            session_time,
                            session_capacity,
                            model):
        return
    
    def join_fl_session(self, session_id):
        return
    
    def session_ack(self):
        return
    
    def leave_session(self, session_id):
        return
    
    def wait_for_updated_model(self):
        return
    
    # def _get_header_body(self , msg) -> list :
    #     header_body = str(msg.payload.decode()).split('::')
    #     print("MESSAGE Header: " + header_body[0])

    #     header_parts = header_body[0].split('|')
    #     return header_parts
