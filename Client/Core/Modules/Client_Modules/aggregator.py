import numpy as np
import torch


class SDFLMQ_Aggregator():
    
    def __init__(self)-> None:
        self.max_clients = {}
        self.client_model_params = {}

    def set_max_agg_capacity(self,session_id,max_clients):
        self.max_clients[session_id] = max_clients
    
    def accumulate_params(self,session_id, params):
        if(session_id not in self.client_model_params):
            self.client_model_params[session_id] = [params]    
        else:
            self.client_model_params[session_id].append(params)
        
        if(len(self.client_model_params[session_id]) >= self.max_clients[session_id]):
            g_model = self.fed_average(session_id)
            return [1,g_model]
        else:
            return [0,None]
        
    def fed_average(self, session_id):
        global_dict = self.client_model_params[session_id][0]
        # print("Length of client model params list: " + str(len(self.client_model_params)))
        num_clients = len(self.client_model_params[session_id])
        for name in global_dict.keys():
            for i in range(1,num_clients):
                # print(global_dict[name])
                # print(self.client_model_params[i][name])
                if(name in self.client_model_params[i]):
                    global_dict[name] += torch.tensor(self.client_model_params[i][name])
            global_dict[name] = global_dict[name] / (num_clients+1)
        # global_model.load_state_dict(global_dict)
        self.client_model_params[session_id] = []
        return global_dict
