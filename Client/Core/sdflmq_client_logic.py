from .Base.executable_class import PubSub_Base_Executable
from .Modules.Client_Modules.aggregator import SDFLMQ_Aggregator
from .Modules.Client_Modules.role_arbiter import Role_Arbiter
from .Modules.model_controller import Model_Controller
from .Base.topics import SDFLMQ_Topics

import numpy as np
import json
from datetime import datetime, timedelta

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

        # os.system('setterm -background yellow -foreground black')
        # os.system('clear')
        self.aggregator     = SDFLMQ_Aggregator()
        self.arbiter        = Role_Arbiter(preferred_role)
        self.controller     = Model_Controller(myID)

        self.executables.extend(['report_resources', 
                                 'receive_global',
                                 'receive_local',
                                 'send_local',
                                 'set_role',
                                 'reset_role',
                                 'set_session_roles',
                                 'session_ack',
                                 'round_ack'])
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port ,
                    loop_forever)
        
        
    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        print("subscribed to coordinator to client public and private topics.")
        self.client.subscribe(self.CoTClT,qos=2)
        self.client.subscribe(self.CoTClT + self.id,qos=2)
        # self.client.subscribe(self.PSTCoT)
        self.client.subscribe(self.PSTCliIDT,qos=2)
        
    def execute_on_msg (self, header_parts, body): 
            super().execute_on_msg(header_parts, body) 

            if header_parts[2] == 'report_resources' :
                resources = self.arbiter.get_resources()
                self.__report_resources(resources)
            
            if header_parts[2] == 'receive_global':
                session_id = body.split(' -s_id ')[1]  .split(' -model_params ')[0]
                model_params = body.split(' -model_params ')[1]  .split(';')[0]
                self.__receive_global(  session_id=session_id,
                                        model_params=model_params)
                
            if header_parts[2] == 'receive_local':
                session_id = body.split(' -s_id ')[1]  .split(' -model_params ')[0]
                model_params = body.split(' -model_params ')[1]  .split(';')[0]
                self.__receive_local(  session_id=session_id,
                                        model_params=model_params)

            if header_parts[2] == 'send_local':
                session_id = body.split(' -s_id ')[1]  .split(';')[0]
                self.__send_local(session_id=session_id)
                
            if header_parts[2] == 'set_role':
                session_id = body.split(' -s_id ')[1]  .split(' -role ')[0]
                role = body.split(' -role ')[1]  .split(' -role_dic ')[0]
                role_dic = body.split(' -role_dic ')[1]  .split(';')[0]
                self.__set_role(session_id=session_id,
                                role=role,
                                role_dic=role_dic)

            if header_parts[2] == 'reset_role':
                session_id = body.split(' -s_id ')[1]  .split(' -role ')[0]
                role = body.split(' -role ')[1]  .split(';')[0]
                self.__reset_role(session_id=session_id,
                                role=role)
            
            # if header_parts[2] == 'set_session_roles':
            #     session_id = body.split(' -s_id ')[1]  .split(' -role_dic ')[0]
            #     role_dic = body.split(' -role_dic ')[1]  .split(';')[0]
            #     self.__set_session_roles(session_id=session_id,
            #                              roles=role_dic)

            if header_parts[2] == 'session_ack':
                session_id = body.split(' -session_id ')[1]  .split(' -ack_type ')[0]
                ack_type = body.split(' -ack_type ')[1]  .split(';')[0]
                
                self.__session_ack( ack_type=ack_type,
                                    session_id=session_id)
            
            if header_parts[2] == 'round_ack':
                session_id = body.split(' -session_id ')[1]  .split(' -ack ')[0]
                ack = body.split(' -ack ')[1]  .split(';')[0]
                self.__round_ack(ack=ack)

    def __report_resources(self,res_msg) -> None : 
        self.publish(topic=self.ClTCoT,func_name="parse_client_stats",msg=res_msg)

    def __receive_global(self,session_id,model_params):
        self.controller.update_model(session_id,model_params)
        if(self.model_update_callback != None):
            self.model_update_callback()
    
    def __receive_local(self,session_id, params):
        if(self.arbiter.is_aggregator):
            model_params = json.loads(params)
            [ack,g_model] = self.aggregator.accumulate_params(session_id,model_params)
            if(ack == 1):
                self.w_aggregation = False
                self.controller.update_model(g_model)

    def __send_local(self,session_id):
        self.send_local(session_id=session_id)
        print("Model parameters published higher level.")
    
    def __set_role(self,session_id,role,role_dic):
        self.__set_session_roles(session_id,role_dic)
        ack = self.arbiter.set_role(session_id,role)
       
        if(ack == 0):
            print("role set successfully")
            if(self.arbiter.is_aggregator or self.arbiter.is_root_aggregator):
                print(role)
                self.aggregator.set_max_agg_capacity(session_id,len(self.arbiter.session_role_dicionaries[session_id][role]) )
                if(self.arbiter.is_aggregator):
                    self.client.subscribe(self.arbiter.get_role(session_id),qos=2)
            self.publish(self.ClTCoT,"confirm_role"," -s_id " + str(session_id) +
                                                    " -c_id " + str(self.id) +
                                                    " -role " + str(role))
  
    def __reset_role(self,session_id,role):
        if(self.arbiter.is_aggregator or self.arbiter.is_root_aggregator):
            self.client.unsubscribe(self.arbiter.get_role(session_id))
        ack = self.arbiter.reset_role(session_id,role)
        if(ack == 0):
            if(self.arbiter.is_aggregator or self.arbiter.is_root_aggregator):
                self.aggregator.set_max_agg_capacity(session_id,len(self.arbiter.session_role_dicionaries[session_id][role]) )
                if(self.arbiter.is_aggregator):
                    self.client.subscribe(self.arbiter.get_role(session_id),qos=2)
            self.publish(self.ClTCoT,"confirm_role"," -s_id " + str(session_id) +
                                                    " -c_id " + str(self.id) +
                                                    " -role " + str(role))
            
    def __session_ack(self, ack_type, session_id):
        if(ack_type == "new_s"):
            self.w_new_session = False
            self.client.subscribe(str(session_id),qos=2)
            print("New session established. Subscribed to the session " + str(session_id))
        if(ack_type == "join_s"):
            self.w_join_session = False
            self.client.subscribe(str(session_id),qos=2)
            print("Successfully joined session. Subscribed to the session " + str(session_id))
            
        if(ack_type == "leave_s"):
            self.w_leave_session = False
            self.client.unsubscribe(str(session_id))
            print("Successfully left session. Unsubscribed from the session.\n")
            
        if(ack_type == "delete_s"):
            self.delete_session = False
            self.client.unsubscribe(str(session_id))
            print("Successfully deleted session. Unsubscribed from the session.\n")
            
        if(ack_type == "active_s"):
            print("Session is active. Now waiting for role...\n")
            
        if(ack_type == "terminate_s"):
            self.client.unsubscribe(str(session_id))
            print("Session terminated. Unsubscribed from the session.\n")
    
    def __round_ack(self, ack): 
        if(ack == "round_ready"):
            self.w_round_ready = False
            print("Round ready. Ready for model contribution\n")
            
        if(ack == "round_complete"):
            self.w_round_complete = False
            print("Round completed. Receiving or should have received new model update\n")
       
    def __set_session_roles(self,session_id,roles):
        print("received session roles: " + str(roles))
        self.arbiter.set_role_dicionary(session_id,roles)

    def __wait_for_response(self):
        if(self.loop_forever):
            return
    
        WAITING1 =  True
        while(WAITING1):
            WAITING1 = (self.w_delete_session or
                      self.w_new_session or
                      self.w_join_session or
                      self.w_terminate_session or
                      self.w_leave_session or
                      self.w_round_ready or
                      self.w_round_complete or
                      self.w_aggregation)
            # print("Waiting...")
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
                            session_id :str,
                            session_time : timedelta,
                            session_capacity_min : int,
                            session_capacity_max : int, 
                            waiting_time : timedelta, 
                            model_name : str,
                            fl_rounds : int,
                            model_spec : str,
                            memcap : float,
                            modelsize : float,
                            preferred_role : str,
                            processing_speed : float,
                            model_update_callback : None):  
        self.model_update_callback = model_update_callback
        self.publish(self.ClTCoT,"create_fl_session",  " -c_id " + str(self.id) + 
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
                                                            " -pspeed " + str(processing_speed))
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
                            processing_speed,
                            model_update_callback):
        self.model_update_callback = model_update_callback
        self.publish(self.ClTCoT,"join_fl_session", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id) + 
                                                            " -fl_rounds " + str(fl_rounds) +
                                                            " -model_name " + str(model_name)+
                                                            " -model_spec " + str(model_spec)+ 
                                                            " -memcap " + str(memcap) + 
                                                            " -mdatasize " + str(modelsize) + 
                                                            " -client_role " + str(preferred_role) + 
                                                            " -pspeed " + str(processing_speed))

        self.arbiter.add_session(session_id)
        self.arbiter.set_current_session(session_id)
        self.__wait_join_session_ack()
        
    def leave_session(self, session_id):
        self.publish(self.ClTCoT,"leave_fl_session", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))

        self.__wait_leave_session_ack()
        
    def delete_session(self, session_id):
        self.publish(self.ClTCoT,"delete_fl_session", " -c_id " + str(self.id) + 
                                                            " -s_id " + str(session_id))
        
        self.__wait_delete_session_ack()
        
    def get_model_spec(self,session_id):
        return self.controller.get_model_spec(session_id)
    
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
            self.publish(self.ClTCoT,"round_complete"," -s_id " + str(session_id) + " -c_id " + str(self.client._client_id))
        else:
            self.publish(self.arbiter.get_session_aggregator(),"receive_local"," -id " + self.id + " -model_params " + str(model_params))
            print("Model parameters published to aggregator.")
    
    def wait_model(self):
        self.__wait_round_complete()

    