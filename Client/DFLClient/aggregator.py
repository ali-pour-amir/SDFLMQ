import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class dflmq_aggregator():
    
    def __init__(self)-> None:
        self. global_model = None
        self.test_dataset = None
        self.executables = ['set_agg_test_dataset', 'agg_test']

    def set_agg_test_dataset(self,dataset):
        self.test_dataset = dataset

    def fedAvg(self, client_models):
        #This function has aggregation method mean
        ### This will take simple mean of the weights of models ###
        global_dict = self.global_model.state_dict()
        for k in global_dict.keys():
            global_dict[k] = torch.stack([client_models[i].state_dict()[k].float() for i in range(len(client_models))], 0).mean(0)
        
        self.global_model.load_state_dict(global_dict)
        for model in client_models:
            model.load_state_dict(self.global_model.state_dict())
            
   
    def agg_test(self, test_dataset):
        """This function test the global model on test data and returns test loss and test accuracy """
        self.global_model.eval()
        test_loss = 0
        correct = 0
        with torch.no_grad():
            for data, target in test_dataset:
                data, target = data, target
                output = self.global_model(data)
                test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
                pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
                correct += pred.eq(target.view_as(pred)).sum().item()

        test_loss /= len(test_dataset)
        acc = correct / len(test_dataset)

        return test_loss, acc
    
    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)

        # if header_parts[2] == '' : 
        #     self.()
