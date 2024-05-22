import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class dflmq_trainer():
    def __init__(self) -> None:
        
        self.executables = ['set_training_dataset']
        self.client_model = None
        self. optimizer = optim.SGD

        # ############### optimizer ################
        # opt = optim.SGD(self.client_model.parameters(), lr=0.1)
    
  
    def set_training_dataset(self,dataset):
        self.training_dataset = dataset

    def client_update(self, training_dataset, round=1):##TODO: Don't forget to reset the optimizer after each round, since it is a class variable.
    #This function updates/trains client model on client data
        self.client_model.train()
        for e in range(round):
            for batch_idx, (data, target) in enumerate(self.training):
                data, target = data, target
                self.optimizer(self.client_model.parameters(), lr=0.1) .zero_grad()
                output = self.client_model(data)
                loss = F.nll_loss(output, target)
                loss.backward()
                self.optimizer.step()
        return loss.item()

    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)

        # if header_parts[2] == '' : 
        #     self.()
        
    
    
