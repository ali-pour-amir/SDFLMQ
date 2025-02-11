import json
import psutil
import os
import psutil

class Role_Arbiter():
    def __init__(self,client_id):

        self.is_aggregator = False
        self.is_root_aggregator = False
        
        self.client_id = client_id
        self.current_session = ""
        self.roles = {} #Keys are session ids
        self.cluster_heads = {}
        self.session_role_dicionaries = {}
    def get_resources(self):
        resources = {
            'cpu_count'     : psutil.cpu_count() ,
            'cpu_frequency' : psutil.cpu_freq() ,
            'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
            # 'net_counters'  : psutil.net_io_counters()
            # 'cpu_stats'     : psutil.cpu_stats() ,
            # 'net_stats'     : psutil.net_if_stats() ,
            # 'disk_usage'    : psutil.disk_usage("/") ,
            }

        res_msg = json.dumps(resources)
        return res_msg
    
    def get_role(self,session_id):
        return self.roles[session_id]

    def set_current_session(self,session_id):
        self.current_session = session_id
        
    def add_session(self,session_id,):
        self.roles[session_id] = ""

    def set_role(self,session_id,role):
        if(session_id in self.roles):
            self.roles[session_id] = role
            
            if(role == "agg_0_" + str(session_id)):
                self.is_aggregator = True
                self.is_root_aggregator = True
                return None
            elif(role[0] == 'a'):
                self.is_aggregator = True
                self.is_root_aggregator = False
            elif(role[0] == 't'):
                self.is_aggregator = False
                self.is_root_aggregator = False
            else:
                print("Unknown role!!")
                return
            
            role_dic = self.session_role_dicionaries[session_id]
            agg_clients = role_dic.keys()
            for agg_c in agg_clients:
                sub_clients = role_dic[agg_c]
                if(role in sub_clients):
                    print("Found matching role in role dictionary. Returning aggregator of the cluster")
                    self.cluster_heads[session_id] = agg_c
                    return agg_c
        else:
            print("No session found with session id: " + str(session_id))
            
    def reset_role(self,session_id,role):
        if(session_id in self.roles):
            self.roles[session_id] = role
            if(role == "agg_0_" + str(session_id)):
                self.is_aggregator = True
                self.is_root_aggregator = True
                return None
            elif(role[0] == 'a'):
                self.is_aggregator = True
                self.is_root_aggregator = False
            elif(role[0] == 't'):
                self.is_aggregator = False
                self.is_root_aggregator = False
            else:
                print("Unknown role!!")
                return
            role_dic = self.session_role_dicionaries[session_id]
            agg_clients = role_dic.keys()
            for agg_c in agg_clients:
                sub_clients = role_dic[agg_c]
                if(role in sub_clients):
                    print("Found matching role in role dictionary. Returning aggregator of the cluster")
                    self.cluster_heads[session_id] = agg_c
                    return agg_c
        else:
            print("No session found with session id: " + str(session_id))

    def set_role_dicionary(self,session_id,roles):
        self.session_role_dicionaries[session_id] = roles 
    
    def get_session_aggregator(self,session_id):
        return self.cluster_heads[session_id]
