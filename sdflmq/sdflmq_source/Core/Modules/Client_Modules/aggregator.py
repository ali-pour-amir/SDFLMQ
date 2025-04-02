import numpy as np
import torch


class SDFLMQ_Aggregator():
    
    def __init__(self)-> None:
        self.max_clients = {}
        self.client_model_params = {}

    def set_max_agg_capacity(self,session_id,max_clients):
        self.max_clients[session_id] = max_clients
    
    def accumulate_params(self,session_id, local_model, params):
        if(session_id not in self.client_model_params):
            self.client_model_params[session_id] = [params]    
        else:
            self.client_model_params[session_id].append(params)
        
        if(len(self.client_model_params[session_id]) >= self.max_clients[session_id]):
            print("number of contributing clients: " + str(len(self.client_model_params[session_id])))
            g_model = self.fed_average(session_id,local_model)
            return [1,g_model]
        else:
            return [0,None]
        
    def fed_average(self,session_id, local_model):
      
        global_dict = {}
        for name, param in local_model.named_parameters():
            global_dict[name] = param.data.tolist()

        # print("Length of client model params list: " + str(len(self.client_model_params)))
        num_clients = len(self.client_model_params[session_id])
        param_names = global_dict.keys()
        for name in param_names:
            for i in range(num_clients):
                # print(global_dict[name])
                # print(self.client_model_params[i][name])
                if(name in self.client_model_params[session_id][i]):
                    layer = self.client_model_params[session_id][i][name]
                    global_dict[name] = torch.tensor(global_dict[name]) + torch.tensor(layer) 
                    # print(global_dict[name])
            global_dict[name] =  global_dict[name] / num_clients
        local_model.load_state_dict(global_dict)
        self.client_model_params[session_id] = []
        return global_dict
