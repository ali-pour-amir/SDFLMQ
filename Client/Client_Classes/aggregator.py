import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms

class dflmq_aggregator():
    
    def __init__(self)-> None:
        self.executables = []
        self.is_aggregator = False
        self.client_model_params = []

        self.current_agg_topic_r = "-1"
        self.current_agg_topic_s = "-1"
    
    def accumulate_params(self, params):
        self.client_model_params.append(params)

    def fed_average(self, global_model):
        
        #This function has aggregation method mean
        ### This will take simple mean of the weights of models ###
        #Append local model params to the list:

        # weights_and_biases = {}
        # for name, param in global_model.named_parameters():
        #     weights_and_biases[name] = param.data.tolist()

        # local_params = []
        # local_params.append({k: v.cpu() for k, v in global_model.state_dict().items()})
        # self.client_model_params.append(weights_and_biases)

        global_dict = global_model.state_dict()
        print("Length of client model params list: " + str(len(self.client_model_params)))
        
        # for k in global_dict.keys():
        #     global_dict[k] = torch.stack([torch.tensor(self.client_model_params[i][k]) for i in range(len(self.client_model_params))],0).mean(0)
        num_clients = len(self.client_model_params)
        for name in global_dict.keys():
            for i in range(num_clients):
                # print(global_dict[name])
                # print(self.client_model_params[i][name])
                if(name in self.client_model_params[i]):
                    global_dict[name] += torch.tensor(self.client_model_params[i][name])
            global_dict[name] = global_dict[name] / (num_clients+1)

        global_model.load_state_dict(global_dict)
        # for model in self.client_model_params:
        #     model.load_state_dict(global_model.state_dict())
        print("Fed_average complete. Clearing model updates, and sharing global model...")
        self.client_model_params = []
        return global_model
   
    def agg_test(self, global_model, test_dataset):
        """This function test the global model on test data and returns test loss and test accuracy """
        
        test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=len(test_dataset), shuffle=True)
        x_test, y_test = next(iter(test_loader))

        global_model.eval()
        test_loss = 0
        correct = 0
        criterion = nn.CrossEntropyLoss()
        with torch.no_grad():
            # for batch_indx, (data, target) in enumerate(test_loader):
            # output = global_model(data)
            # test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            # pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            # correct += pred.eq(target.view_as(pred)).sum().item()
            output = global_model(x_test)
            test_loss = criterion(output, y_test).item()
            pred = output.argmax(dim=1, keepdim=True)
            test_correct = pred.eq(y_test.view_as(pred)).sum().item()
                

        # test_loss /= len(test_dataset)
        acc = test_correct / len(test_dataset)

        print("test loss: " + str(test_loss))
        print("test acc: " + str(acc))
        return acc, test_loss
    
    def _execute_on_msg(self,header_parts, body):
        return 0
        # if header_parts[2] == '' : 
        #     self.()
