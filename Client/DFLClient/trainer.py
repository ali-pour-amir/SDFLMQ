import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class dflmq_trainer():
    def __init__(self) -> None:
        
        self.executables = ['set_training_dataset']
        self.client_model = None
        self. optimizer = optim.SGD(self.client_model.parameters(), lr=0.1) 

        # ############### optimizer ################
        # opt = optim.SGD(self.client_model.parameters(), lr=0.1)
    
  
    def set_training_dataset(self,dataset):
        self.training_dataset = dataset

    def client_update(self, client_model, optimizer, training_dataset, round=1):
    #This function updates/trains client model on client data
        self.client_model.train()
        for e in range(round):
            for batch_idx, (data, target) in enumerate(self.training):
                data, target = data, target
                optimizer.zero_grad()
                output = client_model(data)
                loss = F.nll_loss(output, target)
                loss.backward()
                optimizer.step()
        return loss.item()

    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)

        # if header_parts[2] == '' : 
        #     self.()
        
    
    
