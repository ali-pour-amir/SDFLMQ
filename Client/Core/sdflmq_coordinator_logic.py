from Core.Base.executable_class import PubSub_Base_Executable
from Core.Base.topics import SDFLMQ_Topics
import Core.Modeules.Coordinator_Modules.components as components
from Core.Modules.Coordinator_Modules.session_manager import Session_Manager
from Core.Modules.Coordinator_Modules.clustering_engine import Clustering_Engine
from Core.Modules.Coordinator_Modules.load_balancer import Load_Balancer

import json
import ast
import matplotlib.pyplot as plt
import threading
import random

class DFLMQ_Coordinator(PubSub_Base_Executable) :

    def __init__(self , 
                myID : str , 
                broker_ip : str , 
                broker_port : int , 
                start_loop : bool,
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
        self.executables.append('round_complete')
        # self.executables.append('')
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    start_loop)
        
        self.client.subscribe(self.CiTCoT)
    
    def __parse_client_stats(self , client_id,session_id, statsstr) : 

        stats = json.loads(statsstr)
        round_status = self.active_session['rounds'][self.active_session['current_round']]['status'] 

        if((round_status != 'pending') and (round_status != 'complete')):
            if(client_id in self.client_stats):
                self.client_stats[client_id]['bandwidth'].append(stats['bandwidth'])
                self.client_stats[client_id]['cpu_frequency'].append(stats['cpu_frequency'])
                self.client_stats[client_id]['available_ram'].append(stats['available_ram'])

            else:
                self.client_stats[client_id] = {}
                self.client_stats[client_id]['bandwidth']      =  [stats['bandwidth']]
                self.client_stats[client_id]['cpu_frequency']  =  [stats['cpu_frequency']]
                self.client_stats[client_id]['available_ram']      =  [stats['available_ram']]
                      
    def __broadcast_roles(self,session_id):
        role_dic = json.dumps(self.session_manager.get_session[session_id].role_dictionary)
        self.publish(session_id, "set_session_roles"," -roles " + role_dic)
        
    def order_client_resources(self,model_name, dataset_name) : 
        self.publish(self.CoTClT , "echo_resources" , " -model_name " + model_name + " -dataset_name " + dataset_name)
        
    def Initiate_FL(self):
        self.order_client_resources(self.active_session['model_name'],self.active_session['dataset_name'])

    def save_logs(self):
        session_file = open(self.root_directory + "/"+self.active_session['session_name']+".txt",'w')
        client_stats_file = open(self.root_directory + "/"+self.active_session['session_name']+"_client_stats.txt",'w')
        json.dump(self.active_session,session_file)
        json.dump(self.client_stats,client_stats_file)

    def request_client_stats(self,session_id):
        self.publish(topic=session_id,func_name="report_client_stats",msg="")

    def __round_complete(self, session_id, client_id):
        if(client_id == self.session_manager.get_session(session_id).get_root_node().id): #If client id matching with root aggregator and if session id matching
            self.session_manager.get_session(session_id).complete_round()#Increase round step
            self.publish(topic=session_id,func_name="round_ack",msg="round_complete")#Send ack to clients "round_complete"
                
        if(self.session_manager.get_session(session_id).session_status == components._SESSION_TERMINATED):  #On get_session it is checked if round counter equal to max round of session.
            self.publish(topic=session_id,func_name="session_ack",msg="terminate_s")        #If yes, terminate session, and send ack to clients "session_terminated"
        elif(self.session_manager.get_session(session_id).session_status == components._SESSION_ACTIVE):#If not, and session is still active then:
            self.session_manager.get_session(session_id).new_round()#Set new round
            self.__update_roles(session_id)#Update roles
            
    def __check_session_status(self,session_id):
        if(self.session_manager.get_session(session_id).session_status == components._SESSION_READY):#if session ready, clusterize session, and send ack to clients "session ready"
            self.__clusterize_session(session_id)
            self.publish(topic=session_id,func_name="session_ack",msg="active_s")
        elif(self.session_manager.get_session(session_id).session_status == components._SESSION_TIMEOUT):#if min cap not met, and session time is over, terminate session, and send ack to clients
              self.publish(topic=session_id,func_name="session_ack",msg="terminate_s")

    def __clusterize_session(self,session_id):
        session = self.session_manager.get_session[session_id]
        #1) Create a topology for the session meaning how many agg units are there, and how many nodes are under each agg node. 
        # This set the role_dictionary, and also creates a blank role_vector array.
        self.clustering_engine.create_topology(session)
        #2) Associate clients to nodes. This will fill the role_vector array with client ids.
        self.load_balancer.initialize_roles(session)
        #3) Forms Clusters and also puts Nodes (not clients) into designated Clusters.
        clusters = self.clustering_engine.form_clusters(session)
        session.set_clusters(clusters)
        #Inform Clients in nodes with NODE_PENDING status
        for node in session.nodes:
            if(node.status == components._NODE_PENDING):
                self.publish(topic=self.CoTClT + node.client.id,func_name="set_role",msg=node.role)

        self.__broadcast_roles(session_id)

    def __update_roles(self,session_id):
        session = self.session_manager.get_session[session_id]
        #1) Returns a new role_vector based on the optimizer's suggestion
        #2) Updates the roles according to the new_role_Vector. This only looks into the nodes, and does not need to travers into clusters.
        self.load_balancer.optimize_roles(session)
        #Inform Clients in nodes with NODE_PENDING status
        for node in session.nodes:
            if(node.status == components._NODE_PENDING):
                self.publish(topic=self.CoTClT + node.client.id,func_name="reset_role",msg=node.role)
    
    def __confirm_role(self,session_id,client_id,role):
        ack = self.Session_Manager.get_session(session_id).confirm_role(role,client_id) #Set new role for the client as ready 
        if(ack == 0):
            if(self.session_manager.All_Nodes_Ready(session_id)):#Check all roles, if all are ready, then send ack to clients "round_ready"
                self.publish(topic=session_id,func_name="round_ack",msg="round_ready") 
       
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
                                    mdatasize,
                                    pspeed):
        
        ack = self.session_manager.create_new_session(session_id,
                                                session_time,
                                                session_capacity_min,
                                                session_capacity_max, 
                                                waiting_time, 
                                                model_name,
                                                model_spec,
                                                fl_rounds)
        
        if(ack == 0):
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg="new_s")

        ack2 = self.session_manager.join_session(session_id,
                                                client_id,
                                                client_role,
                                                model_name,
                                                model_spec,
                                                fl_rounds,
                                                memcap,
                                                mdatasize,
                                                pspeed)
        if(ack2 == 0):
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg="join_s")
        
    def __join_fl_session_request(self,
                                    session_id,
                                    client_id,
                                    client_role,
                                    model_name,
                                    model_spec,
                                    fl_rounds,
                                    memcap,
                                    mdatasize,
                                    pspeed):
        
        ack = self.session_manager.join_session(session_id,
                                            client_id,
                                            client_role,
                                            model_name,
                                            model_spec,
                                            fl_rounds,
                                            memcap,
                                            mdatasize,
                                            pspeed)
        
        if(ack == 0):
            self.__check_session_status(session_id)
            self.publish(topic=self.CoTClT + client_id,func_name="session_ack",msg="join_s")
            
    def __execute_on_msg(self, header_parts, body) -> None :
        super().__execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'create_fl_session' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(' -s_time ')[0]
            session_time  = body.split(' -s_time ')[1]  .split(' -s_c_min ')[0]
            session_capacity_min  = body.split(' -s_c_min ')[1]    .split(' -s_c_max ')[0]
            session_capacity_max = body.split(' -s_c_max ')[1]   .split(' -waiting_time ')[0]
            waiting_time     = body.split(' -waiting_time ')[1]   .split(' -model_name ')[0]
            model_name     = body.split(' -model_name ')[1]   .split(' -fl_rounds ')[0]
            fl_rounds     = body.split(' -fl_rounds ')[1]   .split(' -model_spec ')[0]
            model_spec     = body.split(' -model_spec ')[1]   .split(' -memcap ')[0]
            memcap     = body.split(' -memcap ')[1]   .split(' -mdatasize ')[0]
            model_size     = body.split(' -mdatasize ')[1]   .split(' -client_role ')[0]
            preferred_role     = body.split(' -client_role ')[1].split(' -p_speed ')[0]
            processing_speed     = body.split(' -_speed ')[1] .split(';')[0]
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
                                          preferred_role = preferred_role,
                                          processing_speed = processing_speed)

        if header_parts[2] == 'join_fl_session' :  
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(' -s_time ')[0]
            model_name     = body.split(' -model_name ')[1]   .split(' -fl_rounds ')[0]
            fl_rounds     = body.split(' -fl_rounds ')[1]   .split(' -model_spec ')[0]
            model_spec     = body.split(' -model_spec ')[1]   .split(' -memcap ')[0]
            memcap     = body.split(' -memcap ')[1]   .split(' -mdatasize ')[0]
            model_size     = body.split(' -mdatasize ')[1]   .split(' -client_role ')[0]
            preferred_role     = body.split(' -client_role ')[1].split(' -p_speed ')[0]
            processing_speed     = body.split(' -_speed ')[1] .split(';')[0]
            self.__join_fl_session_request(session_id = session_id,
                                           client_id = client_id,
                                           model_name = model_name,
                                           fl_rounds = fl_rounds,
                                           model_spec = model_spec,
                                           memcap = memcap,
                                           model_size = model_size,
                                           preferred_role = preferred_role,
                                           processing_speed = processing_speed)
        
        if header_parts[2] == 'leave_fl_session' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(';')[0]
            print("Leave session has not been implemented yet.")
        
        if header_parts[2] == 'delete_fl_session' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(';')[0]
            print("Delete session has not been implemented yet.")
            
        if header_parts[2] == 'confirm_role' : 
            client_id = body.split(' -c_id ')[1]  .split(' -s_id ')[0]
            session_id  = body.split(' -s_id ')[1]  .split(' -s_time ')[0]
            role     = body.split(' -role ')[1].split(';')[0]
            self.__confirm_role(session_id=session_id,
                                client_id=client_id,
                                role=role)
            
        if header_parts[2] == 'round_complete' : 
            session_id = body.split(' -s_id ')[1]  .split(' -c_id ')[0]
            client_id  = body.split(' -c_id ')[1]  .split(';')[0]
            self.__round_complete(session_id=session_id,
                                  client_id=client_id)
        

