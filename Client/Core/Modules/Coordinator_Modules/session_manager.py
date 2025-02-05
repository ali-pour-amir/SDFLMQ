import numpy as np
import datetime
import Core.Modeules.Coordinator_Modules.components as components

from Core.Modules.Coordinator_Modules.components import Cluster
from Core.Modules.Coordinator_Modules.components import Cluster_Node
from Core.Modules.Coordinator_Modules.components import Session
from Core.Modules.Coordinator_Modules.components import Client

class Session_Manager():
    def __init__(self):
        self.__sessions = {}
    
    def All_Nodes_Ready(self,session_id):
        for n in self.sessions[session_id].nodes:
            if(n.is_elected):
                if(n.status == components._NODE_PENDING):
                    return False
        return True
   
    def update_session(self,session_id):
        if(self.__sessions[session_id].session_creation_time + #Check session Time
           self.__sessions[session_id].session_time > datetime.datetime.now()):
            self.__sessions[session_id].session_status = components._SESSION_TIMEOUT
            print("Session with session_id " + session_id + " reached timeout, and no longer alive")
        if((len(self.__sessions[session_id].client_list) >= self.__sessions[session_id].session_capacity_min)): #Check list of clients, in relation to min capacity and max capacity
            self.__sessions[session_id].session_status = components._SESSION_ACTIVE  #if greater than min cap is met then session ready
            print("Session ready")
            
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
        try:
            new_session = Session(  session_id,
                                    session_time,
                                    session_capacity_min,
                                    session_capacity_max, 
                                    waiting_time, 
                                    model_name,
                                    model_spec,
                                    fl_rounds)
            
            self.sessions[session_id] = new_session
            return 0
        except:
            print("Error occured in new session generation.")
            return -1

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
        try:
            if(session_id in self.sessions):
                if(self.sessions[session_id].model_name == model_name):
                    if(self.sessions[session_id].model_spec == model_spec):
                        new_client = Client(client_id,
                                            client_role,
                                            fl_rounds,
                                            memcap,
                                            mdatasize,
                                            pspeed)
                        self.sessions[session_id].add_client(new_client)
                        return 0
                    else:
                        print("model spec does not match")
                        return -1
                else:
                    print("model name does not match")
                    return -1
            else:
                print("session id does not excist")
                return -1
        except:
            print("error occured in joining client to session.")
            return -1

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
