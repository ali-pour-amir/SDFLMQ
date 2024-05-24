import paho.mqtt.client as mqtt
import time as T
class PubSub_Base_Executable:

#EXECUTABLE PARAMS: 
        
        id = ""
        executables = ['print','echo_name','publish_executables'] #NOTE: Any method that wants to be controller executable, can be added to this list.
        introduction_topic = ''
        controller_executable_topic = ''
        controller_echo_topic = ''

#MQTT PARAMS:
        broker_ip = ''
        broker_port = 0000
        connection_timeout = 60

#SECTION:: STARTUP
        def __init__(self,myID,broker_ip, broker_port, introduction_topic, controller_executable_topic,controller_echo_topic, start_loop):


            self.id = myID
            self.broker_ip = broker_ip
            self.broker_port = broker_port
            self.introduction_topic = introduction_topic
            self.controller_executable_topic = controller_executable_topic
            self.controller_echo_topic = controller_echo_topic

            self.msg_batch_queue = []

            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.execute_on_msg
            self.client.connect(self.broker_ip,
                                self.broker_port,
                                self.connection_timeout)
            
            print("Initiation Done.")

            if(start_loop):
                print("Starting base loop right away.")
                self.base_loop() 
               

#SECTION:: CONNECTIVITY
        def execute_on_msg (self,client,userdata, msg):                             ### TO OVERRIDE IN SUCCEEDING CLASSES

            try:

                #print("MESSAGE: " + msg.payload.decode())
                header_body = str(msg.payload.decode()).split('::')
                print("MESSAGE Header: " + header_body[0])
                header_parts = header_body[0].split('|')

                if(not(header_parts[2] in self.executables)):
                    self.ERROR_executable_not_defined(msg.payload.decode())
                    return

                if header_parts[2] == 'print':
                    body_split = header_body[1].split('-m ')[1].split(';')[0]
                    self.print(body_split)

                if header_parts[2] == 'echo_name':
                    self.echo_name()
                
                if header_parts[2] == 'echo_msg':
                    self.echo_msg(header_body[1])
                
                if header_parts[2] == 'publish_executables':
                    self.publish_executables()    
                
            except:
                print("Message was not right!")

       
        def on_connect(self,client,userdata, flags, rc):
            print("Connected with result code " + str(rc))
            client.subscribe(self.controller_executable_topic)
            print("Subscribed to " + self.controller_executable_topic)

        def MQTT_msg_craft(self,topic,func_name,msg,is_split = False):
            if(is_split):
                payload = self.id +"|" + topic + "|" + func_name + "|" + T.asctime() + "::" + str(msg) + "|" + "is_split" + ":" + "True"
            else:
                payload = self.id +"|" + topic + "|" + func_name + "|" + T.asctime() + "::" + str(msg)
            return payload
        
        def msg_sort_key(self,l):
            return int(l[1])
        
        def MQTT_msg_merge(self,payload_id):
            msg_batches = []
            for batch in self.msg_batch_queue:
                if batch[0] == payload_id:
                    msg_batches.append(batch)

            msg_batches.sort(key=self.msg_sort_key)
            msg_payload = ""
            msg_payload = msg_payload.join(msg_batches)
            return msg_payload


        def MQTT_msg_split(self,msg,batch_size):
            payload_id = 0
            msg_splits = []
            for i in range(0,len(msg),batch_size):
                if((i*batch_size)+batch_size >= len(msg)):
                    msg_splits.append([payload_id,i,msg[(i*batch_size):len(msg)]])
                else:                  
                    msg_splits.append([payload_id,i,msg[(i*batch_size):(i*batch_size)+batch_size]]) #[payload_id, batch_id, msg_payload]
            return [msg_splits]

        def publish(self, topic, func_name, msg):
            payload = self.MQTT_msg_craft(topic,func_name,msg)
            self.client.publish(topic, payload = payload)
#SECTION:: EXECUTABLES
    
        def echo_name(self):
            print("Asking controller to echo my id:" + self.id)
            self.publish(topic=self.controller_echo_topic,func_name="echo_name",msg=self.id)

        def echo_msg(self,msg):
            print("Asking controller to echo my msg: " + msg)
            self.publish(topic=self.controller_echo_topic,func_name="echo_msg",msg=msg)

        def publish_executables(self):                                                                       ### TO OVERRIDE IN SUCCEEDING CLASSES
            msg = ''
            for item in self.executables:
                msg = msg + item + ","
            msg = msg[0:len(msg)-1]
            print("Publishing the list of executables ...")
            self.publish(self.introduction_topic,"publish_executables",msg)

        def print(self,msg):
            print(msg)

#SECTION:: EXECUTION EXCEPTIONS
        def ERROR_executable_not_defined(self,msg):
            print("Executable " + str(msg) + " is not defined.")
        
        def ERROR_executable_param_size_not_defined(self,msg):
            print("Executable " + str(msg) + " has undefined parameter size.")

#SECTION:: MAIN LOOP
        def base_loop(self):
            
            restore_count = 0 # Restoration Cap is 10
            while(True):
                error = ""
                try:
                    self.client.loop_forever()
                except OSError:
                    error = "Executable ran into error: " + OSError.strerror                                                                      
                    self.echo_msg(error)
                    if(restore_count < 10):
                        self.echo_msg("Client " + self.id + " is Restoring program...")
                        restore_count += 1
                        continue
                    else:
                        self.echo_msg("Client " + self.id + " maximum number of restoration reached. Killing instance. Attempt to reinitialize.")
                        return -1
                        



