
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
                 preferred_role: str,
                 loop_forever : bool) -> None : 
        
        topics = SDFLMQ_Topics()
      
        self.ClTCoT = topics.ClTCoT
        # self.PSTCoT = topics.PSTCoT
        self.CoTClT = topics.CoTClT + self.id
        self.PSTCliIDT = topics.PSTCliIDT + self.id
        
        self.w_new_session = False
        self.w_join_session = False
        self.w_leave_session = False
        self.w_delete_session = False
        self.w_terminate_session = False
        self.w_round_ready = False
        self.w_round_complete = False
        self.w_aggregation = False

        os.system('setterm -background yellow -foreground black')
        os.system('clear')
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    loop_forever)
        
        self.aggregator     = SDFLMQ_Aggregator()
        self.arbiter        = Role_Arbiter(preferred_role)
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
        # self.client.subscribe(self.PSTCoT)
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

    def __report_resources(self,res_msg) -> None : 
        self.publish(topic=self.ClTCoT,func_name="parse_client_stats",msg=res_msg)

    def __receive_global(self,session_id,model_params):
        self.controller.set_model(session_id,model_params)
        ###Then call the model_update_callback
        if(self.model_update_callback != None):
            self.model_update_callback()
    
    def __receive_local(self,id, params):
        if(self.arbiter.is_aggregator):
            model_params = json.loads(params)
            self.aggregator.accumulate_params(model_params)
            print("Received and archived client " + id + " local model parameters.")
            self.publish(self.ClTCoT,"aggregator_received_local_params"," -id " + id)
        
    def __send_local(self,logic_model):
        weights_and_biases = {}
        for name, param in logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        model_params = json.dumps(weights_and_biases)
        self.publish(self.aggregator.current_agg_topic_s,"receive_local"," -id " + self.id + " -model_params " + str(model_params))
        print("Model parameters published to aggregator.")
    
    def __reset_role(self,session_id,role):
        ack = self.arbiter.reset_role(session_id,role)
        if(ack == 0):
            self.publish(self.ClTCoT,"confirm_role"," -s_id " + str(session_id) +
                                                    " -c_id " + str(self.id) +
                                                    " -role " + str(role))
            
    def __set_role(self,session_id,role):
        ack = self.arbiter.set_role(session_id,role)
        if(ack == 0):
            self.publish(self.ClTCoT,"confirm_role"," -s_id " + str(session_id) +
                                                    " -c_id " + str(self.id) +
                                                    " -role " + str(role))
        
    def __session_ack(self, ack_type, ack_msg):
        if(ack_type == "new_s"):
            self.w_new_session = False
            print("New session established\n")
        if(ack_type == "join_s"):
            self.w_join_session = False
            print("Successfully joined session\n")
            
        if(ack_type == "leave_s"):
            self.w_leave_session = False
            print("Successfully left session\n")
            
        if(ack_type == "delete_s"):
            self.delete_session = False
            print("Successfully deleted session\n")
            
        if(ack_type == "active_s"):
            print("Session is active. Now waiting for role...\n")
        if(ack_type == "terminate_s"):
            print("Session terminated\n")
    
    def __round_ack(self, ack): 
        if(ack == "round_ready"):
            self.w_round_ready = False
            print("Round ready. Ready for model contribution\n")
            
        if(ack == "round_complete"):
            self.w_round_complete = False
            print("Round completed. Receiving or should have received new model update\n")
       
    def __set_session_roles(self,session,roles):
        self.arbiter.set_role_dicionary(roles)

    def __wait_for_response(self):
        if(self.loop_forever):
            return

        WAITING =   (self.w_delete_session or
                      self.w_new_session or
                      self.w_join_session or
                      self.w_terminate_session or
                      self.w_leave_session or
                      self.w_round_ready or
                      self.w_round_complete or
                      self.w_aggregation)
        
        while(WAITING):
            self.oneshot_loop()
    
    def __wait_for_aggregation(self):
        if(self.arbiter.is_aggregator):
            self.w_aggregation = True
            self.__wait_for_response()

    def __wait_new_session_ack(self):
        self.w_new_session = True
        self.__wait_for_response()
        
    def __wait_join_session_ack(self):
        self.w_join_session = True
        self.__wait_for_response()
        
    def __wait_leave_session_ack(self):
        self.w_leave_session = True
        self.__wait_for_response()
        
    def __wait_delete_session_ack(self):
        self.w_delete_session = True
        self.__wait_for_response()
        
    def __wait_round_ready(self):
        self.w_round_ready = True
        self.__wait_for_response()
        
    def __wait_round_complete(self):
        self.w_round_complete = True
        self.__wait_for_response()
        
    def create_fl_session(self, 
                            session_id,
                            session_time,
                            session_capacity_min,
                            session_capacity_max, 
                            waiting_time, 
                            model_name,
                            fl_rounds,
                            model_spec,
                            memcap,
                            modelsize,
                            preferred_role,
                            prosessing_speed,
                            model_update_callback):  
        print("Creating new session:\n"+
                "Session id:                {session_id},"+
                "Session time:              {session_time},"+
                "Min num of contributors:   {session_capacity_min},"+
                "Max num of contributors:   {session_capacity_max}" +
                "Session waiting time:      {waiting_time}"+
                "FL rounds:                 {fl_rounds}"+
                "Model name:                {model_name}"+
                "Model size:                {modelsize}"+
                "Client role:               {preferred_role}")
        self.model_update_callback = model_update_callback
        self.publish(self.ClTCoT,"new_fl_session_request",  " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id) +
                                                            " -s_time " + str(session_time) +
                                                            " -s_c_min " + str(session_capacity_min) +
                                                            " -s_c_max " + str(session_capacity_max) + 
                                                            " -waiting_time " + str(waiting_time) +
                                                            " -fl_rounds " + str(fl_rounds) + 
                                                            " -model_name " + str(model_name)+
                                                            " -model_spec " + str(model_spec)+ 
                                                            " -memcap " + str(memcap) + 
                                                            " -mdatasize " + str(modelsize) + 
                                                            " -client_role " + str(preferred_role) + 
                                                            " -pspeed " + str(prosessing_speed))
        self.arbiter.add_session(session_id)
        self.arbiter.set_current_session(session_id)
        self.__wait_new_session_ack()
        
    def join_fl_session(self,session_id,
                            preferred_role,
                            model_name,
                            model_spec,
                            fl_rounds,
                            memcap,
                            modelsize,
                            prosessing_speed,
                            model_update_callback):
        print("Joining Session:\n"+
                "Session id:                {session_id},"+
                "Model name:                {model_name}"+
                "Model size:                {modelsize}"+
                "FL rounds:                 {fl_rounds}"+
                "Client role:               {preferred_role}")
        self.model_update_callback = model_update_callback
        self.publish(self.ClTCoT,"join_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id) + 
                                                            " -fl_rounds " + str(fl_rounds) +
                                                            " -model_name " + str(model_name)+
                                                            " -model_spec " + str(model_spec)+ 
                                                            " -memcap " + str(memcap) + 
                                                            " -mdatasize " + str(modelsize) + 
                                                            " -client_role " + str(preferred_role) + 
                                                            " -pspeed " + str(prosessing_speed))

        self.arbiter.add_session(session_id)
        self.arbiter.set_current_session(session_id)
        self.__wait_join_session_ack()
        
    def leave_session(self, session_id):
        self.publish(self.ClTCoT,"leave_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))

        self.__wait_leave_session_ack()
        
    def delete_session(self, session_id):
        self.publish(self.ClTCoT,"delete_fl_session_request", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))
        
        self.__wait_delete_session_ack()
        
    def get_model_spec(self,session_id):
        return self.controller.get_model_spec(session_id)
    
    def add_session(self,session_id,role):
        self.arbiter.add_session(session_id,role)

    def set_current_session(self,session_id):
        self.arbiter.set_current_session(session_id)
    
    def set_model(self,session_id,model):
        self.controller.set_model(session_id,model)
    
    def send_local(self,session_id): 
        self.__wait_for_aggregation()
        
        weights_and_biases = {}
        logic_model = self.controller.get_model(session_id)
        for name, param in logic_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()
        model_params = json.dumps(weights_and_biases)
        
        self.__wait_round_ready()
        
        if(self.arbiter.is_root_aggregator):
            self.publish(self.arbiter.current_session,"receive_global", " -model_params " + str(model_params)) 
            print("Global model parameters published to clients. Informing Coordinator.")
            self.publish(self.ClTCoT,"round_complete","")
        else:
            self.publish(self.aggregator.current_agg_topic_s,"receive_local"," -id " + self.id + " -model_params " + str(model_params))
            print("Model parameters published to aggregator.")
    
    def wait_model(self):
        self.__wait_round_complete()

    