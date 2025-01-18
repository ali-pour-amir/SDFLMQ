import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
class dflmq_trainer():
    def __init__(self) -> None:
        
        self.executables = []
        self.is_trainer = False
        # ############### optimizer ################
        # opt = optim.SGD(self.client_model.parameters(), lr=0.1)

    def client_update(self, training_dataset, client_model, num_epochs, batch_size, round=1):##TODO: Don't forget to reset the optimizer after each round, since it is a class variable.
        if(self.is_trainer == False):
            print("Client is not a trainer!")
            return
        loader = torch.utils.data.DataLoader(dataset=training_dataset, batch_size=len(training_dataset), shuffle=True)
        x_train, y_train = next(iter(loader))

        #This function updates/trains client model on client data
        val_size = int(0.1 * len(training_dataset))
        train_size = len(training_dataset) - val_size
        
        train_data, val_data = torch.utils.data.random_split(
            list(zip(x_train, y_train)), [train_size, val_size])

        
        x_val, y_val = zip(*val_data)
        x_val = torch.stack(x_val)
        y_val = torch.tensor(y_val)

        train_loader = torch.utils.data.DataLoader(dataset=train_data, batch_size=batch_size, shuffle=True)


        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(client_model.parameters(),lr=0.01)

        print("Training begins for " + str(num_epochs) + " epochs ...")
        client_model.train()
        for e in range(num_epochs):
            print("epoch " + str(e))
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data, target
                print("batch " + str(batch_idx))
                optimizer.zero_grad()
                output = client_model(data)
                loss = criterion(output, target)
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
            print(f"Validation accuracy: {val_accuracy:.4f}")

        print("Training done.")
        return client_model
        # Validate the local model
        # client_model.eval()
        # with torch.no_grad():
        #     val_output = client_model(x_val)
        #     val_loss = criterion(val_output, y_val).item()
        #     #*****************
        #     val_pred = val_output.argmax(dim=1, keepdim=True)
        #     val_correct = val_pred.eq(y_val.view_as(val_pred)).sum().item()
        #     val_accuracy = val_correct / len(y_val)
        #     print(f" Client {i + 1} validation accuracy: {val_accuracy:.4f}")
