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
    
    def set_current_session(self,session_id):
        self.current_session = session_id
        

    def add_session(self,session_id,):
        self.roles[session_id] = ""

    def set_role(self,session_id,role):
        if(session_id in self.roles):
            self.roles[session_id] = role
            if(role == "agg_0_" + str(session_id)):
                return None
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
                return None
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

    # def set_aggregator(self,id): #TODO: Move this to the Role Arbiter module
    #     if(id == self.id):
    #         self.aggregator.is_aggregator = True
    #         os.system('setterm -background blue -foreground white')
    #         os.system('clear')
    #         if(self.aggregator.current_agg_topic_r != "-1"):
    #             self.client.unsubscribe(self.aggregator.current_agg_topic_r)
    #         self.aggregator.current_agg_topic_r = "c2a_agg_"+id
    #         self.aggregator.current_agg_topic_s = "a2c_agg_"+id
    #         self.client.subscribe(self.aggregator.current_agg_topic_r)
    #     else:
    #         self.aggregator.is_aggregator = False
    #         os.system('setterm -background yellow -foreground black')
    #         os.system('clear')
    #         if(self.aggregator.current_agg_topic_r != "-1"):
    #             self.client.unsubscribe(self.aggregator.current_agg_topic_r)
    #         self.aggregator.current_agg_topic_s = "c2a_agg_"+id
    #         self.aggregator.current_agg_topic_r = "a2c_agg_"+id
    #         self.client.subscribe(self.aggregator.current_agg_topic_r)
    #     print("Aggregator topic: " + str(self.aggregator.is_aggregator))
