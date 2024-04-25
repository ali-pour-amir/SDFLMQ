#Here, the core modules of MQTT Fleet Control is placed
import broker_manager
import clients_manager
import executable_manager
import paho.mqtt.client as mqtt
import os
import threading
import json
import time as T
from MQTTFC_Procedures import MQTTFC_Procedures

class Server_Controller:
    
    
    sub_topics_directory = "metadata/topics_to_subscribe.json"
    pub_topics_directory = "metadata/topics_to_publish.json"

    broker_mtf_directory = "metadata/broker_metadata.json"
    client_mtf_directory = "metadata/client_metadata.json"
    
    registered_executables = []
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    MQTT_thread_handler = threading.Thread(target=client.loop_forever)
    
    def __init__(self,log_func):

        self.broker_list = self.Load_brokers()
        self.selected_broker = self.broker_list[0]
        self.my_procedures = MQTTFC_Procedures()

        #self.client_list = self.Load_clients()
        self.client_list = []

        self.sub_topics = self.load_topics_to_subscribe()
        self.pub_topics = self.load_topics_to_publish()
        
        if(log_func != None):
            self.log = log_func
        else:
            self.log = self.Log

    def Subscribe_to_All(self):
        for topic in self.sub_topics:
            self.Subscribe(topic_name=topic)

    def Subscribe(self,topic_name):
        self.client.subscribe(topic=topic_name)
        print("Subscribed to topic " + topic_name)
        self.log ("CONTROLLER::CORE:: " + "Subscribed to topic " + topic_name)
    
    def Connect_to_Selected_Broker(self,on_connect_func, on_message_func):
        try:
            if(not self.MQTT_thread_handler.is_alive()):
                self.client.on_connect = on_connect_func
                self.client.on_message = on_message_func
        
                self.log("CONTROLLER::CORE:: connecting to " + str(self.selected_broker))
                
                self.client.connect(self.selected_broker[0],self.selected_broker[1],self.selected_broker[2])
                self.MQTT_thread_handler.start()

            else:
                self.log("CONTROLLER::CORE:: Dashboard already connected to a broker. Close the dashboard and start again.")
        
        except:
                self.log("CONTROLLER::CORE:: Error in connecting to the broker. Or no broker is selected.")
            

    def Client_PowerOn(self,c_index,callback):
        return 0
            
    def Client_PowerOff(self,c_index,callback):
        return 0
        
    def Load_brokers(self):
        brkr_mtf = open(self.broker_mtf_directory)
        data = json.load(brkr_mtf)
        broker_list = []
        for item in data:
            broker_list.append([item['ip'],int(item['port']),int(item['timeout'])])
        return broker_list

    def load_topics_to_subscribe(self):
        f = open(self.sub_topics_directory)
        data = json.load(f)
        topic_list = []
        for item in data:
            topic_list.append(item)
        return topic_list
    
    def load_topics_to_publish(self):
        f = open(self.pub_topics_directory)
        data = json.load(f)
        topic_list = []
        for item in data:
            topic_list.append(item)
    
    def Load_clients(self):
        client_mtf = open(self.client_mtf_directory)
        data = json.load(client_mtf)
        c_list = []
        for item in data:
            c_list.append(clients_manager.Client(name=item['name'],
                                                           id=item['id'],
                                                           type=item['type'],
                                                           directory=item['directory'],
                                                           broker=item['broker']))
        return c_list
    
    
    def message_parse(self,msg):
        msg_parts = msg.split("::")
        header_part = msg_parts[0].split('|')
        usr_msg = msg_parts[1]

        if(header_part[2] == "publish_executables"):
            if(header_part[1] == "client_introduction"):
                executables = usr_msg.split(',')
                self.manage_executables(header_part[0],executables_list=executables)
                self.manage_client(header_part[0],executables)
            else:
                self.log("CONTROLLER::CORE:: Publish Executable is sent through unmatching topic. Should be sent through client_introduction.")

        elif(header_part[2] == "echo_name"):            
            self.log("CONTROLLER::CORE:: Echoing " + header_part[0])
        
        elif(header_part[2] == "echo_msg"):            
            self.log("CONTROLLER::CORE:: Echoing " + usr_msg)
        
        else:
            self.log("CONTROLLER::CORE:: No definted Controller function in the message")

    def manage_client(self,client_id,executables):
        for client in self.client_list:
            if (client.id == client_id):
                self.log("CONTROLLER::CORE:: Client already registered.")
                return 0
                
        self.client_list.append(clients_manager.Client(client_id,client_id,"","",self.selected_broker[0],executables=executables))
        
    def manage_executables(self,user_id, executables_list):
        for exec_item in executables_list:
            exists = 0
            for reg_exec_item in self.registered_executables:
                if (reg_exec_item == exec_item):
                    exists = 1
                    break
            if(exists == 0):
                self.registered_executables.append(exec_item)
    

    def MQTT_msg_craft(self,topic,func_name,msg):
            payload = "MQTT_FC" +"|" + topic + "|" + func_name + "|" + T.asctime() + "::" + str(msg)
            return payload


    def Log(self,msg):
        print(msg)

#____________________________________ THE ONLY BASELINE HARDCODED EXECUTABLES THAT ARE KNOWN TO THE CONTROLLER BY DEFAULT::
    def Pub_Clients_Introduce(self):
        self.client_list.clear()
        msg = self.MQTT_msg_craft("controller_executable","publish_executables","asking to publish your executables")
        print(msg)

        self.client.publish("controller_executable",payload = msg)
    
    def Pub_Clients_Echo_Name(self):
        msg = self.MQTT_msg_craft("controller_executable","echo_name","asking to echo your name")
        print(msg)
        
        self.client.publish("controller_executable",payload = msg) 
##    NOTE: THERE SHOULD BE NO OTHER PRE-KNOWN EXECUTABLES THAT ARE CODED. ONLY INTRODUCED TO THE CONTROLLER DURING RUN TIME.
#___________________________________________________________________________________________________________________________

    def Command_Parser(self, commandline):
        rawText = commandline + ';'
        command_parts = rawText.split(' ')

        if(command_parts[0] == "run"):
            command = command_parts[1].split(';')[0] 
            if(command in self.registered_executables):
                msg = ""
                for i in range(len(command_parts)-1):
                    msg = msg + command_parts[i+1] + " "
                pl = self.MQTT_msg_craft("controller_executable",command,msg)
                self.client.publish("controller_executable",payload = pl) 
                #self.log("CONTROLLER:: executable " + command + " published.")
                self.log("CONTROLLER:: PUBLISHED " + commandline)
            else:
                self.log("CONTROLLER:: executable " + command + " not defined.")

        elif(command_parts[0] == "runp"):
            command = command_parts[1].split(';')[0] 
            self.log("CONTROLLER:: procedure " + command + " initiated.")
            self.my_procedures.parse_procedure_command(command,rawText,self.Command_Parser)
           
        else:
            self.log("CONTROLLER::INPUT>> " + commandline)