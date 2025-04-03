# SDFLMQ: A Semi-Decentralized Federated Learning Framework over Publish/Subscribe Communication

**Semi-Decentralized Federated Learning over MQTT (SDFLMQ)** is a federated learning framework with a special focus on distributing the load of aggregation to the contributing client machines. MQTT is used at the core of the framework to manage C2C communication.

The framework utilizes the topic-based communication model in Publish/Subscribe communication protocols to perform dynamic clustering and to balance the load of model aggregation over several contributing clients. With this framework, a group of inter-connected nodes can perform both local and global model updating in synchronization. This elevates the need for a central server with excessive cost to perform the aggregation and global model update.

---

## Architecture

### MQTT Fleet Control

SDFLMQ is based on a tailor-made remote function call (RFC) infrastructure called **MQTT Fleet Control (MQTTFC)**. This lightweight RFC infrastructure binds clients' remotely executable functions to MQTT topics. Any remote client can publish to the function topic and pass the arguments within the message payload, and the function will be called in the client system that has the corresponding function and has subscribed to that function’s topic.

### SDFLMQ Components

The core components of sdflmq are the client logic and the coordinator logic. The client logic contains all the modules and logic behind role arbitration between training and aggregation, and the actual aggregation of the model parameters. The coordinator logic contains the modules used for the orchestration of the clients' contribution as trainers and aggregators, session management, clustering, and load balancing. Both coordinator and client logic controllers are based on the MQTT Fleet Control's base executable logic, which publicizes certain internal functions of the base class and the classes that are inherited from it. 

Aside from that, client modules can be found under the Core/Modules/Clint_Modules, which comprise the role_arbiter module and aggregator module. The coordinator modules also can be found  in Core/Modules/Coordinator_Modules, which comprise the clustering_engine, load_balancer, and session_manager. In addition to the coordinator modules, the optimizers are defined which are used on demand to perform role_association and clustering efficiently. The optimizers are independent scripts that are placed in Core/Modules/Coordinator_Modules/optimizers.

A parameter server logic is also provided as an additional component under development, which can be used for model organizational purposes. The parameter server is a specification of MQTT fleet control's base executable class, which has a singular module used for global update synchronization. The functionality of sdflmq to run FL rounds however does not depend on this logic. Only the client logic and coordinator logic are essential to the core functionality of sdfmlq regarding core FL operation.

---

## Installation
In the following, guidelines are provided to install and integrate SDFLMQ and it's dependencies. Ubuntu 18.xx or higher is considered the default operating system. Nonetheless, SDFLMQ itself is not depended on Ubuntu or any other operating system. Dependencies however may depend, or follow different installation and integration steps. Link for further information on how some of the core dependencies can be integrated are provided which may provide information on installation in other operating systems.

### SDFLMQ Installation

To use the framework, you can clone the GitHub project first:

```bash
git clone https://github.com/ali-pour-amir/SDFLMQ.git
```

While in the SDFLMQ root directory, the framework can be installed using the following command:

```bash
cd SDFLMQ
pip install -e .
```

### MQTT with Mosquitto

SDFLMQ does not depend on any specific MQTT broker implementation. However, it is commonly tested with Mosquitto for local testing and simulation. 
You may install Mosquitto if you wish to use the local system as the broker. To install the broker 

To install Mosquitto you can use the following command:

```bash
sudo apt-get install mosquitto
```
To run the broker as a service, you can use the following command:

```bash
systemctl start mosquitto
```

To stop the Mosquitto broker service, you can use the following command:

```bash
systemctl stop mosquitto
```

You can follow the link below also for further instructions on how to install Mosquitto on other operation systems, using different package managers:
https://mosquitto.org/download/

### EMQX Paho Client

To provide SDFLMQ with communication using publish/subscribe, we integrated the EMQX Paho client. This library is already included in the list of dependencies in the setup.py file.
To alter the EMQX installation, you may first remove the EMQX Paho Client library from the list of dependencies in the setup.py file, then follow the instructions here:
https://www.emqx.com/en/blog/how-to-use-mqtt-in-python

---

## Example with MNIST Dataset

Here we present a sample SDFLMQ setup to collectively train a multi-layer perceptron model on the MNIST dataset. We set a session for 4 clients to perform 10 FL rounds. Following are steps to take to setup the clients' program, the coordinator program, and the code snippets.

### Coordinator

To enable SDFLMQ, a coordinator must be invoked first. One can simply create a script and instantiate from the coordinator logic class like in the following:

```python
from sdflmq import DFLMQ_Coordinator
import time

coordinator_client = DFLMQ_Coordinator(myID      = 'my_coordinator',
                                    broker_ip    = 'localhost' ,
                                    broker_port  = 1883,
                                    loop_forever = True,
                                    plot_stats   = False)

```

The above coordinator connects to a locally running broker service through port number 1883.

A default coordinator similar to the above is also installed with the SDFLMQ installation. You can invoke a coordinator to connect to a local broker using the following bash command:

```bash
sdflmq_coordinator --coordinator_id my_coord_id --broker_ip localhost --broker_port 1883
```

### Initiator Client

Once the coordinator is running, clients can begin their contribution. To do so, an FL session must first be created. This is up to an initiator client who will use the create_fl_session function.

An FL client class must first be instantiated:

```python
myid = "client_" + str(random.randint(0,10000))         
fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)
```

The above client instantiation indicates that the client wants to contribute as an aggregator as well. The initiator client then can use the create_fl_session function to issue a request for creating a session to the coordinator:

```python
fl_client.create_fl_session(session_id=session_name,
                            session_time=timedelta(hours=1),
                            session_capacity_min= 5,
                            session_capacity_max= 5,
                            waiting_time=timedelta(minutes=10),
                            fl_rounds=FL_ROUNDS,
                            model_name="mlp",
                            preferred_role="aggregator")
```

Above is an example of a session for a maximum of 5 contributing clients, with the model name "mlp", and a dedicated session name with a given FL_ROUNDS.


### Joining Client

A joining client will follow the similar steps, however, instead of requesting to create a session, it will issue a request to join a session. Of course this means that the session must be created first and in the list of active sessions on the coordinator side. Therefore, chronologically, the initiator client must run first.

The joining client will do the following steps:

```python
myid = "client_" + str(random.randint(0,10000))

fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)

fl_client.join_fl_session(session_id=session_name,
                                fl_rounds=FL_ROUNDS,
                                model_name="mlp",
                                preferred_role="aggregator")
```

### Update Loop

Once the session is established, the client can commence with the update loops. The way the update loop is conveyed is arbitrary. One trivial way is to do an FL update every X number of local epochs. Here we set X as 5, and so after 5 local training epochs, the clients will send their model parameters to their corresponding aggregator. Note that the destination of the aggregator per client is given at the session initiation. The FL update loop would look like this:

```python
fl_client.set_model(session_name,model)
fl_client.send_local(session_name)
fl_client.wait_global_update()
```

### Submit model stat

One additional step which is optional also can be done to inform the client of the model performance. This data should be submitted by one of the contributing clients. In this example, we give it to the initiator client to submit it at the testing phase:


```python
fl_client.submit_model_stats(session_name,k,accuracy,loss.item())
```


## Full scripts

The full script of the MNIST test case can be found in the following:

### Initiator Client

```python
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
FL_ROUNDS = 10
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

def printsomething():
        print("Model update received")
myid = "client_" + str(random.randint(0,10000))         
fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)
fl_client.create_fl_session(session_id=session_name,
                            session_time=timedelta(hours=1),
                            session_capacity_min= 5,
                            session_capacity_max= 5,
                            waiting_time=timedelta(minutes=10),
                            fl_rounds=FL_ROUNDS,
                            model_name="mlp",
                            preferred_role="aggregator")


for k in range(FL_ROUNDS):
    # Training Loop
    num_epochs = 5
    loss = 0
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


    #Sending the Model for Aggregation
    
    fl_client.set_model(session_name,model)
    fl_client.send_local(session_name)
    fl_client.wait_global_update()

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
    fl_client.submit_model_stats(session_name,k,accuracy,loss.item())
```

### Joining Client

```python
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
FL_ROUNDS = 10
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

```


## MQTTFC Dashboard

*Explain the steps to run and use the MQTTFC dashboard.*

---

## Docker Setup

*Instructions for using Docker to run the SDFLMQ framework.*

# Citation

*Provide reference blocks for citation in both Latex and Docx document formats.*
