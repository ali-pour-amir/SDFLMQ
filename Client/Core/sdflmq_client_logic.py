
from Base.executable_class import PubSub_Base_Executable
from Modules.Client_Modules.aggregator import SDFLMQ_Aggregator
from Modules.Client_Modules.role_arbiter import Role_Arbiter
from Modules.model_controller import Model_Controller

from Base.topics import SDFLMQ_Topics

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
        
        topics = SDFLMQ_Topics()
      
        self.ClTCoT = topics.ClTCoT
        # self.PSTCoT = topics.PSTCoT
        self.CoTClT = topics.CoTClT + self.id
        self.PSTCliIDT = topics.PSTCliIDT + self.id

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
        self.client.subscribe(self.PSTCliIDT)

    def __execute_on_msg (self, header_parts, body): 
        
        # try:
            super().execute_on_msg(header_parts, body) 
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

    def __receive_local(self,id, params):
        model_params = json.loads(params)
        self.aggregator.accumulate_params(model_params)
        print("Received and archived client " + id + " local model parameters.")
        self.publish(self.ClTCoT,"aggregator_received_local_params"," -id " + id)
        ###TODO: then call the model_update_callback
    
    def __send_local(self,logic_model):
        weights_and_biases = {}
        for name, param in logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        model_params = json.dumps(weights_and_biases)
        self.publish(self.aggregator.current_agg_topic_s,"receive_local"," -id " + self.id + " -model_params " + str(model_params))
        print("Model parameters published to aggregator.")
    
    def __propagate_global(self): 
        weights_and_biases = {}
        for name, param in self.client_logic.logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        model_params = json.dumps(weights_and_biases)
        print(len(model_params))
        self.publish(self.aggregator.current_agg_topic_s,"collect_logic_model"," -id " + self.id + " -model_params " + str(model_params)) 
        print("Global model parameters published to clients. Informing Coordinator.")
        self.publish(self.ClTCoT,"global_model_propagated","")
    
    def __report_resources(self,res_msg) -> None : 
        self.publish(topic=self.ClTCoT,func_name="parse_client_stats",msg=res_msg)
    
    def __reset_role(self,role):#TODO:complete logic
        
        #TODO: send confirm role to coordinator
        return
    
    def __set_role(self,role):#TODO:complete logic

        #TODO: send confirm role to coordinator
        return
    
    def __session_ack(self, ack_type):
        if(ack_type == "new_s"):#TODO:complete logic
            return
        if(ack_type == "join_s"):#TODO:complete logic
            return
        if(ack_type == "leave_s"):#TODO:complete logic
            return
        if(ack_type == "delete_s"):#TODO:complete logic
            return
        if(ack_type == "active_s"):#TODO:complete logic
            return
        if(ack_type == "terminate_s"):#TODO:complete logic
            return
    
    def __round_ack(self, ack_type): 
        if(ack_type == "round_ready"):#TODO:complete logic
            return
        if(ack_type == "round_complete"):#TODO:complete logic
            return
       
    def __get_session_roles(self,roles):
        #TODO:complete logic
        return

    def create_fl_session(self, #TODO:complete logic
                            session_id,
                            session_time,
                            session_capacity_min,
                            session_capacity_max,
                            waiting_time, #For both FL round contribution and session joining
                            model_name,
                            model_update_callback):
        
        print("Creating new session with session id:{session_id},"+
               "session time: {session_time},"+
               "min num of contributors: {session_capacity_min},"+
               "max num of contributors: {session_capacity_max}" + "waiting time: {waiting_time}"+
               "model name: {model_name}")
        
        self.model_update_callback = model_update_callback

        self.publish(self.ClTCoT,"new_fl_session_request",  " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id) +
                                                            " -s_time " + str(session_time) +
                                                            " -s_c_min " + str(session_capacity_min) +
                                                            " -s_c_max " + str(session_capacity_max) + 
                                                            " -waiting_time " + str(waiting_time) +
                                                            " -fl_rounds " + str(fl_rounds) + 
                                                            " -model_name " + str(model_name)+
                                                            " model_spec " + str(model_spec)+ 
                                                            " memcap " + str(memcap) + 
                                                            " mdatasize " + str(modelsize) + 
                                                            " pspeed " + str(processing_speed))

    def join_fl_session(self, session_id, rounds, role):#TODO:complete logic and input parameters

        self.publish(self.ClTCoT,"join_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id) + 
                                                            " -s_rounds " + str(rounds) +
                                                            " -c_role " + str(role))
    
    def leave_session(self, session_id):#TODO:complete logic
        
        self.publish(self.ClTCoT,"leave_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))
    
    def delete_session(self, session_id):#TODO:complete logic
        self.publish(self.ClTCoT,"delete_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))
    
    def initiate_session(self, session_id):#TODO:complete logic
        
        self.publish(self.ClTCoT,"leave_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))
    