import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
class dflmq_trainer():
    def __init__(self) -> None:
        
        self.executables = []

        # ############### optimizer ################
        # opt = optim.SGD(self.client_model.parameters(), lr=0.1)

    def client_update(self, training_dataset, client_model, round=1):##TODO: Don't forget to reset the optimizer after each round, since it is a class variable.
       
    #This function updates/trains client model on client data
        val_size = int(0.1 * len(training_dataset))
        train_size = len(training_dataset) - val_size
        train_data, val_data = torch.utils.data.random_split(
            list(zip(x_train, y_train)), [train_size, val_size])

        x_train, y_train = zip(*train_data)
        x_val, y_val = zip(*val_data)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(client_model.parameters(),lr=0.01)
       
        for round in range(round):

            print(f"Round {round + 1}")
            client_weights = []
            for i, (client_x, client_y) in enumerate(training_dataset):

                client_model.train()
                for epoch in range(1):

                    optimizer.zero_grad()
                    output = client_model(client_x)
                    loss = criterion(output, client_y)
                    loss.backward()
                    optimizer.step()
                
                # Validate the local model
                client_model.eval()
                with torch.no_grad():
                    val_output = client_model(x_val)
                    val_loss = criterion(val_output, y_val).item()
                    #*****************
                    val_pred = val_output.argmax(dim=1, keepdim=True)
                    val_correct = val_pred.eq(y_val.view_as(val_pred)).sum().item()
                    val_accuracy = val_correct / len(y_val)
                    print(f" Client {i + 1} validation accuracy: {val_accuracy:.4f}")

    def _execute_on_msg(self,header_parts, body):
        return 0
        # if header_parts[2] == '' : 
        #     self.()
        
    
    
