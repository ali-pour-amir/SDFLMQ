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
        
        self.executables.append('order_client_resources')
        self.executables.append('parse_client_stats')
        self.executables.append('new_training_session')
        self.executables.append('initiate_fl')
        self.executables.append('local_training_complete')
        self.executables.append('aggregation_complete')
        self.executables.append('aggregator_received_local_params')
        self.executables.append('global_model_propagated')

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
        self.publish(session_id, "get_session_roles"," -roles " + role_dic)
        
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
                self.publish(topic=self.topics.CoTClT + node.client.id,func_name="set_role",msg=node.role)

        self.__broadcast_roles(session_id)

    def __update_roles(self,session_id):
        session = self.session_manager.get_session[session_id]
        #1) Returns a new role_vector based on the optimizer's suggestion
        #2) Updates the roles according to the new_role_Vector. This only looks into the nodes, and does not need to travers into clusters.
        self.load_balancer.optimize_roles(session)
        #Inform Clients in nodes with NODE_PENDING status
        for node in session.nodes:
            if(node.status == components._NODE_PENDING):
                self.publish(topic=self.topics.CoTClT + node.client.id,func_name="reset_role",msg=node.role)
    
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
            self.publish(topic=self.topics.CoTClT + client_id,func_name="session_ack",msg="new_s")

        ack2 = self.session_manager.join_session(session_id,
                                            client_id,
                                            model_name,
                                            model_spec,
                                            fl_rounds,
                                            memcap,
                                            mdatasize,
                                            pspeed)
        if(ack2 == 0):
            self.publish(topic=self.topics.CoTClT + client_id,func_name="session_ack",msg="join_s")
        
    def __join_fl_session_request(self,
                                    session_id,
                                    client_id,
                                    model_name,
                                    model_spec,
                                    fl_rounds,
                                    memcap,
                                    mdatasize,
                                    pspeed):
        
        ack = self.session_manager.join_session(session_id,
                                            client_id,
                                            model_name,
                                            model_spec,
                                            fl_rounds,
                                            memcap,
                                            mdatasize,
                                            pspeed)
        
        if(ack == 0):
            self.__check_session_status(session_id)
            self.publish(topic=self.topics.CoTClT + client_id,func_name="session_ack",msg="join_s")
            
    def __execute_on_msg(self, header_parts, body) -> None :
        super().__execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'initiate_fl' : 
            self.Initiate_FL()

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources(self.active_session['model_name'],self.active_session['dataset_name'])

        if header_parts[2] == 'parse_client_stats' : 
            self.parse_client_stats( header_parts[0],body)

        if header_parts[2] == 'new_training_session':
            
            session_name    = body.split(' -session_name ')[1]  .split(' -dataset_name ')[0]
            dataset_name    = body.split(' -dataset_name ')[1]  .split(' -model_name ')[0]
            model_name      = body.split(' -model_name ')[1]    .split(' -num_clients ')[0]
            num_clients     = body.split(' -num_clients ')[1]   .split(' -num_epochs ')[0]
            num_epochs     = body.split(' -num_epochs ')[1]   .split(' -batch_size ')[0]
            batch_size     = body.split(' -batch_size ')[1]   .split(' -num_rounds ')[0]
            num_rounds      = body.split(' -num_rounds ')[1]    .split(';')[0]
            self.create_new_session(session_name,
                                    dataset_name,
                                    model_name,
                                    num_clients,
                                    num_epochs,
                                    batch_size,
                                    num_rounds)

        if(header_parts[2] == 'local_training_complete'):
            client_id = body.split(' -id ')[1].split(' -mem ')[0]
            mem_usage = int(body.split(' -mem ')[1].split(';')[0])

            self.mem_usage_track[client_id].append(mem_usage)
            if(len(self.total_mem_usage[client_id]) > 0):
                self.total_mem_usage[client_id].append(mem_usage + self.total_mem_usage[client_id][len(self.total_mem_usage[client_id])-1])
            else:
                self.total_mem_usage[client_id].append(mem_usage)
            
            
            # model_acc = body.split(' -model_acc ')[1].split(' -model_loss ')[0]
            # model_loss = body.split(' -model_loss ')[1].split(';')[0]
            print("checking client " + client_id + " as its training for the round is finished.")
            self.check_participant(client_id,
                                #    model_acc,
                                #    model_loss
                                   )

        if(header_parts[2] == 'aggregator_received_local_params'):
            client_id = body.split(' -id ')[1].split(';')[0]
            if(client_id in self.active_session['rounds'][self.active_session['current_round']]['participants']):
                print("Aggregator received model params of client " + client_id)
                self.clients_sent_local_params[client_id] = 1
                if(len(self.clients_sent_local_params) == len(self.active_session['rounds'][self.active_session['current_round']]['participants'])):
                    print("All clients sent their locals. Initiating aggregation.")
                    self.clients_sent_local_params = {}
                    self.Prepare_Aggregation()
            else:
                print("not in the list")
        
        if(header_parts[2] == 'aggregation_complete'):
            client_id = body.split(' -id ')[1].split(' -model_acc ')[0]
            model_acc = body.split(' -model_acc ')[1].split(' -model_loss ')[0]
            model_loss = body.split(' -model_loss ')[1].split(' -mem ')[0]
            
            mem_usage = int(body.split(' -mem ')[1].split(';')[0])
            self.mem_usage_track[client_id][len(self.mem_usage_track[client_id])-1] += mem_usage 
            self.total_mem_usage[client_id][len(self.total_mem_usage[client_id])-1] += mem_usage 
           

            self.active_session['rounds'][self.active_session['current_round']]['acc'] = str(model_acc)
            self.active_session['rounds'][self.active_session['current_round']]['loss'] = str(model_loss)
            print("Client " + client_id + " has reported aggregation is complete. Requesting for global model propagation.")

            if(self.plot_stats == True):
                self.plot_accloss(model_acc,model_loss,0,False)
                
            self.publish(self.CoTClT,"propagate_global","")
        
        if(header_parts[2] == 'global_model_propagated'):
            print("Global model propagated. Completing round.")
            self.update_rounds()

