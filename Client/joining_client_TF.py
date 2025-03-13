import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision import datasets, transforms
from Core.sdflmq_client_logic import SDFLMQ_Client
import random
import time
from datetime import datetime, timedelta
from torch.utils.data import Subset

class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(28 * 28, 256)  # Input layer (784 -> 256)
        self.fc2 = nn.Linear(256, 128)      # Hidden layer (256 -> 128)
        self.fc3 = nn.Linear(128, 10)       # Output layer (128 -> 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = x.view(-1, 28 * 28)  # Flatten the image
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)  # No activation on last layer (logits for CrossEntropyLoss)
        return x
FL_ROUNDS = 11
session_name = "session_02"
# Load MNIST dataset
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
full_train_dataset = torchvision.datasets.MNIST(root='./data', train=True, transform=transform, download=True)
test_dataset = torchvision.datasets.MNIST(root='./data', train=False, transform=transform, download=True)

num_samples = int(0.01 * len(full_train_dataset)) 
subset_indices = torch.randperm(len(full_train_dataset))[:num_samples]  # Randomly select indices
train_dataset = Subset(full_train_dataset, subset_indices)
# DataLoaders
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=64, shuffle=False)
# Initialize Model, Loss Function, and Optimizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MLP().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


myid = "client_" + str(random.randint(0,10000))
def printsomething():
        print("Model update received")
fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)
fl_client.join_fl_session(session_id=session_name,
                                fl_rounds=FL_ROUNDS,
                                model_name="mlp",
                                preferred_role="aggregator")

for k in range(FL_ROUNDS):
    # Training Loop
    num_epochs = 5
    for epoch in range(num_epochs):
        model.train()
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}")

    #Joining session for aggregation
    fl_client.set_model(session_name,model)
    fl_client.send_local(session_name)
    fl_client.wait_global_update()
    # model = fl_client.get_model('session_01')


# Testing the Model
model.eval()
correct = 0
total = 0
with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

accuracy = 100 * correct / total
print(f"Test Accuracy: {accuracy:.2f}%")

# LOOPING = True
# while(LOOPING):
#     fl_client.oneshot_loop()
#     time.sleep(1)



