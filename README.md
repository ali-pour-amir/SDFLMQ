# SDFLMQ

**Semi-Decentralized Federated Learning over MQTT (SDFLMQ)** is a federated learning framework with a special focus on distributing the load of aggregation to the contributing client machines. MQTT is used at the core of the framework to manage C2C communication.

The framework utilizes the topic-based communication model in Publish/Subscribe communication protocols to perform dynamic clustering and to balance the load of model aggregation over several contributing clients. With this framework, a group of inter-connected nodes can perform both local and global model updating in synchronization. This elevates the need for a central server with excessive cost to perform the aggregation and global model update.

---

## Architecture

### MQTT Fleet Control

SDFLMQ is based on a tailor-made remote function call (RFC) infrastructure called **MQTT Fleet Control (MQTTFC)**. This lightweight RFC infrastructure binds clients' remotely executable functions to MQTT topics. Any remote client can publish to the function topic and pass the arguments within the message payload, and the function will be called in the client system that has the corresponding function and has subscribed to that function’s topic.

### SDFLMQ Components

*To be completed — include explanations of the main components involved in SDFLMQ.*

---

## Integration

### Installation and Setup

*Provide installation steps and dependencies here.*

### MQTT with Mosquitto

*Explain how to configure and use the Mosquitto MQTT broker.*

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
