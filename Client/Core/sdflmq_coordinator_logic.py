from .Base.executable_class import PubSub_Base_Executable
from .Base.topics import SDFLMQ_Topics
from .Modules.Coordinator_Modules import components as components
from .Modules.Coordinator_Modules.session_manager import Session_Manager
from .Modules.Coordinator_Modules.clustering_engine import Clustering_Engine
from .Modules.Coordinator_Modules.load_balancer import Load_Balancer
import datetime
import json
import ast
import matplotlib.pyplot as plt
import threading
import random
import time

class DFLMQ_Coordinator(PubSub_Base_Executable) :

    def __init__(self , 
                myID : str , 
                broker_ip : str , 
                broker_port : int , 
                loop_forever : bool,
                plot_stats : bool) -> None : 
        
        topics = SDFLMQ_Topics()
        self.CoTClT = topics.CoTClT # publish 
        self.CiTCoT = topics.ClTCoT # subscribe

        self.session_manager = Session_Manager()
        self.clustering_engine = Clustering_Engine()
        self.load_balancer = Load_Balancer()
        
        self.executables.append('create_fl_session')
        self.executables.append('join_fl_session')
        self.executables.append('leave_fl_session')
        self.executables.append('delete_fl_session')
        self.executables.append('confirm_role')
        self.executables.append('client_received_global')
        self.executables.append('submit_model_stat')

        # self.executables.append('')
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port ,
                    loop_forever)
            
    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.client.subscribe(self.CiTCoT,qos=2) 
        print("subscribed to client_to_coordinator topic.")
    
    def __submit_model_stat(self,session_id,client_id,round,acc,loss):
        session = self.session_manager.get_session(session_id)
        # r = session.current_round_index
        r = round
        if(client_id in session.rounds[r]['participants']):
            session.rounds[r]['acc'] = acc
            session.rounds[r]['loss'] = loss
            self.session_manager.save_session_to_file(session_id,self.root_directory)
        else:
            print("client " + str(client_id) + " who wants to submit model stats is not in the list of participants in round " + str(r) + " of sessoin " + str(session_id))

    def __broadcast_roles(self,session_id): #TODO: set retain flag true for this one for other joining clients.
        role_dic = json.dumps(self.session_manager.get_session(session_id).role_dictionary)
        # print(role_dic)
        self.publish(session_id, "set_session_roles"," -s_id " + str(session_id) + " -role_dic " + str(role_dic))
        
    def order_client_resources(self,model_name, dataset_name) : 
        self.publish(self.CoTClT , "echo_resources" , " -model_name " + model_name + " -dataset_name " + dataset_name)
        
    
    def request_client_stats(self,session_id):
        self.publish(topic=session_id,func_name="report_client_stats",msg="")

    def __client_received_global(self,session_id,client_id):
        # print("client " + str(client_id) + " received global for session id: " + str(session_id))
        for c in self.session_manager.get_session(session_id).client_list:
            if(client_id == c.client_id): #If client id matching with root aggregator and if session id matching
                self.session_manager.get_session(session_id).add_participant(client_id)#Increase round step
                if(len(self.session_manager.get_session(session_id).get_participants()) == self.session_manager.get_session(session_id).get_current_round()['num_registered_clients']): #Fix this
                    print("Flagging round as complete.")
                    self.session_manager.get_session(session_id).complete_round()
                    self.session_manager.update_session(session_id)
                    # print(self.session_manager.get_session(session_id).session_status)
                    self.publish(topic=session_id,func_name="round_ack",msg=" -session_id " + str(session_id) + " -ack round_complete")#Send ack to clients "round_complete"
                    if(self.session_manager.get_session(session_id).session_status == components._SESSION_TERMINATED):  #On get_session it is checked if round counter equal to max round of session.
                        print("Session terminated")
                        session = self.session_manager.get_session(session_id)
                        session.session_termination_time = datetime.datetime.now()
                        session.total_processing_time = session.session_termination_time - session.session_creation_time
                        self.session_manager.save_session_to_file(session_id,self.root_directory)
                        self.publish(topic=session_id,func_name="session_ack",msg= " -session_id " + str(session_id) + " -ack_type terminate_s")        #If yes, terminate session, and send ack to clients "session_terminated"
                    elif(self.session_manager.get_session(session_id).session_status == components._SESSION_ACTIVE):#If not, and session is still active then:
                        print("Updating session with new round and updating roles.")
                        self.session_manager.get_session(session_id).new_round()#Set new round
                        self.__update_roles(session_id)
                break
            
    # def __round_complete(self, session_id, client_id):
    #     if(client_id == self.session_manager.get_session(session_id).get_root_node().client.client_id): #If client id matching with root aggregator and if session id matching
    #         self.session_manager.get_session(session_id).complete_round()#Increase round step
    #         self.publish(topic=session_id,func_name="round_ack",msg=" -session_id " + str(session_id) + " -ack round_complete")#Send ack to clients "round_complete"
                
    #     if(self.session_manager.get_session(session_id).session_status == components._SESSION_TERMINATED):  #On get_session it is checked if round counter equal to max round of session.
    #         self.publish(topic=session_id,func_name="session_ack",msg= " -session_id " + str(session_id) + " -ack_type terminate_s")        #If yes, terminate session, and send ack to clients "session_terminated"
    #     elif(self.session_manager.get_session(session_id).session_status == components._SESSION_ACTIVE):#If not, and session is still active then:
    #         pass
    #         self.session_manager.get_session(session_id).new_round()#Set new round
    #         self.__update_roles(session_id)#Update roles
            
    def __check_session_status(self,session_id):
        if(self.session_manager.get_session(session_id).session_status == components._SESSION_ACTIVE):#if session ready, clusterize session, and send ack to clients "session ready"
            if(self.session_manager.get_session(session_id).current_round_index == 0):
                self.__clusterize_session(session_id)
            # else:
            #     self.__update_roles(session_id)

            self.publish(topic=session_id,func_name="session_ack",msg=" -session_id " + str(session_id) + " -ack_type active_s")
        elif(self.session_manager.get_session(session_id).session_status == components._SESSION_TIMEOUT):#if min cap not met, and session time is over, terminate session, and send ack to clients
              self.publish(topic=session_id,func_name="session_ack",msg=" -session_id " + str(session_id) + " -ack_type terminate_s")

    def __clusterize_session(self,session_id):
        session = self.session_manager.get_session(session_id)
        self.clustering_engine.create_2layer_topology(session,0.3)
        # print("sessions role dictionary: " + str(session.role_dictionary))
        role_dic = json.dumps(session.role_dictionary)
        clusters = self.clustering_engine.form_clusters(session)
        session.set_clusters(clusters)
        roles_vector = self.load_balancer.random_initialize_roles(session)
        # print(roles_vector)
        session.set_roles(roles_vector)
        # print("len nodes: " + str(len(session.nodes)))
        for node in session.nodes:
            # print(node.role)
            if(node.status == components._NODE_PENDING):
                time.sleep(1)
                self.publish(topic=self.CoTClT + node.client.client_id,func_name="set_role",msg= " -s_id " + str(session_id) + " -role " + str(node.role)+ " -role_dic " + str(role_dic))

    def __update_roles(self,session_id):
        # print("updating roles")
        session = self.session_manager.get_session(session_id)
        #1) Returns a new role_vector based on the optimizer's suggestion
        #2) Updates the roles according to the new_role_Vector. This only looks into the nodes, and does not need to travers into clusters.
        self.load_balancer.randomly_update_roles(session)
        #Inform Clients in nodes with NODE_PENDING status
        no_pending_roles = True
        for node in session.nodes:
            # print(node.role)
            if(node.status == components._NODE_PENDING):
                # time.sleep(1)
                no_pending_roles = False
                print("Notifying clients with new roles\n")
                self.publish(topic=self.CoTClT + node.client.client_id,func_name="reset_role",msg= " -s_id " + str(session_id) + " -role " + str(node.role))
        if(no_pending_roles):
            [ack2,num_active_nodes] = self.session_manager.All_Nodes_Ready(session_id)
            if(ack2):#Check all roles, if all are ready, then send ack to clients "round_ready"
                self.session_manager.get_session(session_id).get_current_round()['num_registered_clients'] = num_active_nodes
                self.publish(topic=session_id,func_name="round_ack",msg=" -session_id " + str(session_id) + " -ack round_ready") 
                # print("published round ready\n")
    
    def __confirm_role(self,session_id,client_id,role):
        # print("confriming role\n")
        ack = self.session_manager.get_session(session_id).confirm_role(role,client_id) #Set new role for the client as ready 
        if(ack == 0):
            [ack2,num_active_nodes] = self.session_manager.All_Nodes_Ready(session_id)
            if(ack2):#Check all roles, if all are ready, then send ack to clients "round_ready"
                self.session_manager.get_session(session_id).get_current_round()['num_registered_clients'] = num_active_nodes
                self.publish(topic=session_id,func_name="round_ack",msg=" -session_id " + str(session_id) + " -ack round_ready") 
                # print("published round ready\n")
       
    def __new_fl_session_request(self,
                                    session_id,
                                    session_time,
                                    session_capacity_min,
                                    session_capacity_max, 
                                    waiting_time, 
                                    model_name,
                                    fl_rounds,
                                    client_id,
                                    client_role,
                                    model_spec,
                                    memcap,
                                    model_size,
                                    pspeed):
        print("Received request for new session\n")
        ack = self.session_manager.create_new_session(session_id,
                                                session_time,
                                                session_capacity_min,
                                                session_capacity_max, 
                                                waiting_time, 
                                                model_name,
                                                model_spec,
                                                fl_rounds)
        
        if(ack == 0):
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg=" -session_id " + str(session_id) + " -ack_type new_s")

        ack2 = self.session_manager.join_session(session_id,
                                                client_id,
                                                client_role,
                                                model_name,
                                                model_spec,
                                                fl_rounds,
                                                memcap,
                                                model_size,
                                                pspeed)
        if(ack2 == 0):
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg=" -session_id " + str(session_id) + " -ack_type join_s")
        
    def __join_fl_session_request(self,
                                    session_id,
                                    client_id,
                                    client_role,
                                    model_name,
                                    model_spec,
                                    fl_rounds,
                                    memcap,
                                    model_size,
                                    pspeed):
        
        ack = self.session_manager.join_session(session_id,
                                            client_id,
                                            client_role,
                                            model_name,
                                            model_spec,
                                            fl_rounds,
                                            memcap,
                                            model_size,
                                            pspeed)
        print("Received request for joining session " + str(session_id) + "\n")
        if(ack == 0):
            self.__check_session_status(session_id)
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg=" -session_id " + str(session_id) + " -ack_type join_s")
    
    def execute_on_msg(self, header_parts, body):
        super().execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)
        if header_parts[2] == 'create_fl_session' : 
            client_id = body.split(' -c_id ')[1].split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(' -s_time ')[0]
            session_time  = body.split(' -s_time ')[1]  .split(' -s_c_min ')[0]
            session_capacity_min  = body.split(' -s_c_min ')[1]    .split(' -s_c_max ')[0]
            session_capacity_max = body.split(' -s_c_max ')[1]   .split(' -waiting_time ')[0]
            waiting_time     = body.split(' -waiting_time ')[1]   .split(' -fl_rounds ')[0]
            fl_rounds     = body.split(' -fl_rounds ')[1]   .split(' -model_name ')[0]
            model_name     = body.split(' -model_name ')[1]   .split(' -model_spec ')[0]
            model_spec     = body.split(' -model_spec ')[1]   .split(' -memcap ')[0]
            memcap     = body.split(' -memcap ')[1]   .split(' -mdatasize ')[0]
            model_size     = body.split(' -mdatasize ')[1]   .split(' -client_role ')[0]
            preferred_role     = body.split(' -client_role ')[1].split(' -pspeed ')[0]
            processing_speed     = body.split(' -pspeed ')[1] .split(';')[0]
            # batch_size     = body.split(' - ')[1]   .split(' - ')[0]
            # num_rounds      = body.split(' - ')[1]    .split(';')[0]
            self.__new_fl_session_request(session_id = session_id,
                                          client_id = client_id,
                                          session_time = session_time,
                                          session_capacity_min = session_capacity_min,
                                          session_capacity_max = session_capacity_max,
                                          waiting_time = waiting_time,
                                          model_name = model_name,
                                          fl_rounds = fl_rounds,
                                          model_spec = model_spec,
                                          memcap = memcap,
                                          model_size = model_size,
                                          client_role = preferred_role,
                                          pspeed = processing_speed)

        if header_parts[2] == 'join_fl_session' :  
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(' -fl_rounds ')[0]
            fl_rounds     = body.split(' -fl_rounds ')[1]   .split(' -model_name ')[0]
            model_name     = body.split(' -model_name ')[1]   .split(' -model_spec ')[0]
            model_spec     = body.split(' -model_spec ')[1]   .split(' -memcap ')[0]
            memcap     = body.split(' -memcap ')[1]   .split(' -mdatasize ')[0]
            model_size     = body.split(' -mdatasize ')[1]   .split(' -client_role ')[0]
            preferred_role     = body.split(' -client_role ')[1].split(' -pspeed ')[0]
            processing_speed     = body.split(' -pspeed ')[1] .split(';')[0]
            self.__join_fl_session_request(session_id = session_id,
                                           client_id = client_id,
                                           model_name = model_name,
                                           fl_rounds = fl_rounds,
                                           model_spec = model_spec,
                                           memcap = memcap,
                                           model_size = model_size,
                                           client_role = preferred_role,
                                           pspeed = processing_speed)
        
        if header_parts[2] == 'leave_fl_session' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(';')[0]
            print("Leave session has not been implemented yet.")
        
        if header_parts[2] == 'delete_fl_session' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(';')[0]
            print("Delete session has not been implemented yet.")
            
        if header_parts[2] == 'confirm_role' : 
            session_id = body.split(' -s_id ')[1]  .split(' -c_id ')[0]
            client_id = body.split(' -c_id ')[1]  .split(' -role ')[0]
            role     = body.split(' -role ')[1].split(';')[0]
            self.__confirm_role(session_id=session_id,
                                client_id=client_id,
                                role=role)
            
        if header_parts[2] == 'client_received_global' : 
            session_id = body.split(' -s_id ')[1]  .split(' -c_id ')[0]
            client_id  = body.split(' -c_id ')[1]  .split(';')[0]
            self.__client_received_global(  session_id=session_id,
                                            client_id=client_id)
            
        if header_parts[2] == 'submit_model_stat' : 
            session_id = body.split(' -s_id ')[1]  .split(' -c_id ')[0]
            client_id  = body.split(' -c_id ')[1]  .split(' -round ')[0]
            round = int(body.split(' -round ')[1]  .split(' -acc ')[0])
            acc = float(body.split(' -acc ')[1]  .split(' -loss ')[0])
            loss  = float(body.split(' -loss ')[1]  .split(';')[0])
            
            self.__submit_model_stat(session_id,client_id,round,acc,loss)
            
        # if header_parts[2] == 'round_complete' : 
        #     session_id = body.split(' -s_id ')[1]  .split(' -c_id ')[0]
        #     client_id  = body.split(' -c_id ')[1]  .split(';')[0]
        #     self.__round_complete(session_id=session_id,
        #                           client_id=client_id)
        
        # print("parsed the message")
