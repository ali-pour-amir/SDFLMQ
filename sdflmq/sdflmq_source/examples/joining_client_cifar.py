import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import random
from Core.sdflmq_client_logic import SDFLMQ_Client
import random
import time
from datetime import datetime, timedelta
from torch.utils.data import Subset
# Define device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load CIFAR-10 dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)

# Shuffle dataset before sampling
indices = list(range(len(trainset)))
random.shuffle(indices)
subset_size = int(0.1 * len(trainset))  # 10% of the dataset
subset_indices = indices[:subset_size]
train_subset = torch.utils.data.Subset(trainset, subset_indices)

trainloader = torch.utils.data.DataLoader(train_subset, batch_size=64, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=False, num_workers=2)

# Define the CNN model
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
        self.conv5 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.conv6 = nn.Conv2d(256, 256, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(4 * 4 * 256, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 10)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = torch.relu(self.conv3(x))
        x = torch.relu(self.conv4(x))
        x = self.pool(x)
        x = torch.relu(self.conv5(x))
        x = torch.relu(self.conv6(x))
        x = self.pool(x)
        x = x.view(-1, 4 * 4 * 256)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x
    
FL_ROUNDS = 50
session_name = "session_14_cifar"
# Create model, loss function, and optimizer
model = CNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
def printsomething():
        print("Model update received")
myid = "client_" + str(random.randint(0,10000)) 
fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)
fl_client.join_fl_session(session_id=session_name,
                                fl_rounds=FL_ROUNDS,
                                model_name="cifar10_cnn",
                                preferred_role="aggregator")



for k in range(FL_ROUNDS):
    print("Round " + str(k))
    # # Training Loop
    # num_epochs = 2
    # for epoch in range(num_epochs):
    #     running_loss = 0.0
    #     for inputs, labels in trainloader:
    #         inputs, labels = inputs.to(device), labels.to(device)
    #         optimizer.zero_grad()
    #         outputs = model(inputs)
    #         loss = criterion(outputs, labels)
    #         loss.backward()
    #         optimizer.step()
    #         running_loss += loss.item()
    #     print(f"Epoch {epoch+1}, Loss: {running_loss/len(trainloader):.4f}")
    
    #Sending the Model for Aggregation    
    fl_client.set_model(session_name,model)
    fl_client.send_local(session_name)
    fl_client.wait_global_update()


    # # Test phase using 100 samples from the test dataset
    # test_subset_size = 100
    # test_indices = list(range(len(testset)))
    # random.shuffle(test_indices)
    # test_subset_indices = test_indices[:test_subset_size]
    # test_subset = torch.utils.data.Subset(testset, test_subset_indices)
    # testloader_subset = torch.utils.data.DataLoader(test_subset, batch_size=100, shuffle=False)

    # correct = 0
    # total = 0
    # model.eval()
    # with torch.no_grad():
    #     for inputs, labels in testloader_subset:
    #         inputs, labels = inputs.to(device), labels.to(device)
    #         outputs = model(inputs)
    #         _, predicted = torch.max(outputs, 1)
    #         total += labels.size(0)
    #         correct += (predicted == labels).sum().item()

    # print(f"Test Accuracy on 100 samples: {100 * correct / total:.2f}%")
