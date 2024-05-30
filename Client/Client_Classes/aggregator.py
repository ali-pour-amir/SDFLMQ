import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class dflmq_aggregator():
    
    def __init__(self)-> None:
        self.executables = []
        self.is_aggregator = False
        self.client_model_params = []

    def fed_average(self, global_model):
        #This function has aggregation method mean
        ### This will take simple mean of the weights of models ###
        global_dict = global_model.state_dict()
        for k in global_dict.keys():
            global_dict[k] = torch.stack([self.client_model_params[i].state_dict()[k].float() for i in range(len(self.client_model_params))], 0).mean(0)
        
        global_model.load_state_dict(global_dict)
        for model in self.client_model_params:
            model.load_state_dict(global_model.state_dict())
            
   
    def agg_test(self, global_model, test_dataset):
        """This function test the global model on test data and returns test loss and test accuracy """
        self.global_model.eval()
        test_loss = 0
        correct = 0
        with torch.no_grad():
            for data, target in test_dataset:
                data, target = data, target
                output = global_model(data)
                test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
                pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
                correct += pred.eq(target.view_as(pred)).sum().item()

        test_loss /= len(test_dataset)
        acc = correct / len(test_dataset)

        return test_loss, acc
    
    def _execute_on_msg(self,header_parts, body):
        return 0
        # if header_parts[2] == '' : 
        #     self.()
