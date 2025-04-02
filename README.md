# SDFLMQ
Semi-Decentralized Federated Learning over MQTT (SDFLMQ) is a federated learning framework with a special focus on distributing the load of aggregation to the contributing client machines. MQTT is used at the core of the framework to manage C2C communication. The framework utilizes the topic-based communication model in Publish/Subscribe communication protocols to perform dynamic clustering and to balance the load of model aggregation over several contributing clients. With this framework, a group of inter-connected nodes can perform both local and global model updating in synchronization. This elevates the need for a central server with excessive cost to perform the aggregation and global model update.

#Architecture

##MQTT Fleet Control
SDFLMQ is based on a tailor-made remote function call (RFC) infrastructure called MQTT Fleet Control (MQTTFC). This lightweight RFC infrastructure simply binds clients' remotely executable functions to MQTT topics. Thus, any remote client can publish to the function topic and pass the arguments within the message payload, and the function will be called in the client system which has the corresponding function and has subscribed to the topic of that function. 


##SDFLMQ Components


#Integration

##Installation and Setup

##MQTT with Mosquitto

##EMQX Paho client

##Coordinator

##Initiator Client

##Joining Client

#Example with MNIST dataset

#Docker setup
