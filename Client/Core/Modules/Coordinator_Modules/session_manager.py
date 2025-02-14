import numpy as np
import datetime
import matplotlib.pyplot as plt
from . import components as components 

from ..Coordinator_Modules.components import Cluster
from ..Coordinator_Modules.components import Cluster_Node
from ..Coordinator_Modules.components import Session
from ..Coordinator_Modules.components import Client

class Session_Manager():
    def __init__(self):
        self.__sessions = {}
    
    def All_Nodes_Ready(self,session_id):
        active_nodes = 0
        for n in self.__sessions[session_id].nodes:
            # if(n.is_elected):
                if(n.status == components._NODE_ACTIVE):
                    active_nodes += 1
        # if(active_nodes == len(self.__sessions[session_id].nodes)):
        if((active_nodes == self.__sessions[session_id].session_capacity_max) or 
           ((active_nodes >= self.__sessions[session_id].session_capacity_min) and 
            (datetime.datetime.now() > self.__sessions[session_id].get_current_round()['starting_time'] + self.__sessions[session_id].waiting_time))):
            return [True, active_nodes]
        else:
            return [False, active_nodes]
   
    def update_session(self,session_id):

        print("Current round index: " + str(self.__sessions[session_id].current_round_index))
        print("Max rounds: " + str(self.__sessions[session_id].num_rounds))
        
        if(self.__sessions[session_id].current_round_index >= self.__sessions[session_id].num_rounds):
            # print("Session terminated for reaching max fl rounds")
            self.__sessions[session_id].session_status = components._SESSION_TERMINATED
            return

        if(self.__sessions[session_id].session_creation_time + #Check session Time
           self.__sessions[session_id].session_time < datetime.datetime.now()):
            if((len(self.__sessions[session_id].client_list) >= self.__sessions[session_id].session_capacity_min)): #Check list of clients, in relation to min capacity and max capacity
                self.__sessions[session_id].session_status = components._SESSION_ACTIVE  #if greater than min cap is met then session ready
                return
                # print("Session ready")
            else:
                self.__sessions[session_id].session_status = components._SESSION_TIMEOUT
                return
                # print("Session with session_id " + session_id + " reached timeout, and no longer alive")

        elif((len(self.__sessions[session_id].client_list) == self.__sessions[session_id].session_capacity_max)): #Check list of clients, in relation to min capacity and max capacity
            self.__sessions[session_id].session_status = components._SESSION_ACTIVE  #if greater than min cap is met then session ready
            return
            # print("Session ready")
        
        
        
            
    def get_session(self,session_id):
        self.update_session(session_id)
        return self.__sessions[session_id]
    
    def create_new_session(self,
                            session_id,
                            session_time,
                            session_capacity_min,
                            session_capacity_max, 
                            waiting_time, 
                            model_name,
                            model_spec,
                            fl_rounds):
        # try:
            new_session = Session(  session_id,
                                    session_time,
                                    session_capacity_min,
                                    session_capacity_max, 
                                    waiting_time, 
                                    model_name,
                                    model_spec,
                                    fl_rounds)
            
            self.__sessions[session_id] = new_session
            return 0
        # except:
        #     print("error occured in new session generation.")
        #     return -1

    def join_session(self,
                     session_id,
                     client_id,
                     client_role,
                     model_name,
                     model_spec,
                     fl_rounds,
                     memcap,
                     mdatasize,
                     pspeed):
        # try:
            if(session_id in self.__sessions):
                if(self.__sessions[session_id].num_rounds == int(fl_rounds)):
                    if(self.__sessions[session_id].model_name == model_name):
                        if(self.__sessions[session_id].model_spec == model_spec):
                            if(len(self.__sessions[session_id].client_list) < self.__sessions[session_id].session_capacity_max):
                                new_client = Client(client_id,
                                                    client_role,
                                                    fl_rounds,
                                                    memcap,
                                                    mdatasize,
                                                    pspeed)
                                self.__sessions[session_id].add_client(new_client)
                                return 0
                            else:
                                print("ERROR: session is full.")
                                return -1
                        else:
                            print("ERROR: model spec does not match")
                            # print(self.__sessions[session_id].num_rounds)
                            # print()
                            return -2
                    else:
                        print("ERROR: model name does not match")
                        return -3
                else:
                    print("ERROR: number of FL rounds does not match.")
                    return -4
            else:
                print("ERROR: session id does not excist")
                return -5
        # except:
        #     print("error occured in joining client to session.")
        #     return -5

    def plot_accloss(self,acc,loss, rounds = 0, init = False):
      
        if(init == True): 
            self.plot_fig, (self.plot_ax_accloss, self.plot_ax_mem,self.plot_ax_total_mem) = plt.subplots(3,1,layout='constrained') # fig : figure object, ax : Axes object
            self.plot_ax_accloss.set_xlabel('round')
            self.plot_ax_accloss.set_xlim((0,rounds))
            
            self.plot_ax_accloss.set_ylim((0.0,1.0))
            self.plot_ax_accloss.set_ylabel('prediction accuracy')

            self.plot_ax_mem.set_xlim((0,rounds))
            self.plot_ax_mem.set_ylabel('ram usage (bytes)')
            self.plot_ax_mem.set_xlabel('round')

            self.plot_ax_total_mem.set_xlim((0,rounds))
            self.plot_ax_total_mem.set_ylabel('total ram usage (bytes)')
            self.plot_ax_total_mem.set_xlabel('round')
            
            self.plt_step = []
            self.plt_acc = []
            self.plt_loss = []
        else:
            self.plt_step.append(len(self.plt_step))
            self.plt_acc.append(float(acc))
            self.plt_loss.append(float(loss))
           
        # plt.plot(self.plt_step,self.plt_loss,color='red')

        self.plot_ax_accloss.plot(self.plt_step,self.plt_loss,color='red')
        self.plot_ax_accloss.plot(self.plt_step,self.plt_acc,color='blue')
        
        for cl in self.mem_usage_track:
            self.plot_ax_mem.plot(self.plt_step,self.mem_usage_track[cl])

        for cl in self.total_mem_usage:
            self.plot_ax_total_mem.plot(self.plt_step,self.total_mem_usage[cl])
       
        plt.pause(0.1)
        
        # plt.show()
