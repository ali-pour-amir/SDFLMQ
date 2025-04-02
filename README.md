# SDFLMQ: A Semi-Decentralized Federated Learning Framework over Publish/Subscribe Communication Model

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

The framework then can be installed using the following command:

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

*Details on using the EMQX Paho MQTT client with SDFLMQ.*

---

## Example with MNIST Dataset

*Provide a walkthrough or link to an example using the MNIST dataset for demonstration.*

### Coordinator

*Describe the role and setup of the Coordinator node.*

### Initiator Client

*Details about the Initiator Client — responsibilities and setup.*

### Joining Client

*Explain how new clients can join and participate in the learning process.*

### MQTTFC Dashboard

*Explain the steps to run and use the MQTTFC dashboard.*

---

## Docker Setup

*Instructions for using Docker to run the SDFLMQ framework.*

# Citation

*Provide reference blocks for citation in both Latex and Docx document formats.*
