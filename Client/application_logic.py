import Global.custom_models
from Global.custom_models import VGG,MNISTMLP
from trainer import dflmq_trainer
from dflmq_client import DFLMQ_Client
import json
import torch
from io import BytesIO
import base64
import zlib
import tracemalloc
from Global import base_io

class dflmq_client_app_logic():
    
    def __init__(self, is_simulating,id,root_directory)-> None:

        self.id = id
        self.is_simulating = is_simulating
        self.root_directory = self.id+"_data"
        self.logic_model = None
        self.logic_model_name = ""
        self.simulated_logic_data_train = None
        self.simulated_logic_data_test = None
        self.simulated_logic_dataset_name = None
        self.trainer        = dflmq_trainer()
    
        self.executables = ['construct_logic_model', 'collect_logic_model', 'collect_logic_data', 'load_model', 'load_dataset']

        self.dflmq_client = DFLMQ_Client()

        userID = input("Enter UserID: ")
        print("User with ID : " + userID +" is created.")

        exec_program = DFLMQ_Client(myID = userID,
                                    broker_ip = 'localhost' ,
                                    broker_port = 1883,
                                    introduction_topic='client_introduction',
                                    controller_executable_topic='controller_executable',
                                    controller_echo_topic="echo",
                                    start_loop=False)
        exec_program.base_loop()

    def load_model(self, model_name):
        dir = self.root_directory + "/models/"
        data = base_io.load_file(dir,model_name)
        if(data != -1):
            self.logic_model = data
            self.logic_model_name = model_name
            print("Model " + model_name + " loaded.")
    
    def load_dataset(self,dataset_name):
        dir = self.root_directory + "/datasets/"
        data1 = base_io.load_file(dir,dataset_name+"_training")
        data2 = base_io.load_file(dir,dataset_name+"_testing")
        if(data1 != -1):
            self.simulated_logic_dataset_name = dataset_name 
            self.simulated_logic_data_train = data1
            print("Training dataset loaded. set size: " + str(len(data1)))
        if(data2 != -1):
            self.simulated_logic_data_test = data2
            print("Test dataset loaded. set size: " + str(len(data2)))
    
    def construct_logic_model(self, model_name, model_params):
        self.logic_model = Global.custom_models.get_model_class(model_name)
        self.logic_model_name = model_name

        self.collect_logic_model(model_params)

        dir = self.root_directory + "/models/"
        base_io.save_file(dir,model_name,self.logic_model)
    
    def collect_logic_model(self, parameters):
        print(len(parameters))
        weights_and_biases = json.loads(parameters)
        for name, param in self.logic_model.named_parameters():
            if name in weights_and_biases:
                param.data = torch.tensor(weights_and_biases[name])
    
    def collect_logic_data(self,dataset_name, type, bin_data):
        print("performing data collection")

        decoded_compressed_data = base64.b64decode(bin_data.encode('utf-8'))
        decompressed_data = zlib.decompress(decoded_compressed_data)
        buffer_from_string = BytesIO(decompressed_data)
        loaded_dataset = torch.load(buffer_from_string)
        
        self.simulated_logic_data_train = loaded_dataset["trainset"]
        self.simulated_logic_dataset_name = dataset_name  
        self.simulated_logic_data_test = loaded_dataset["testset"]
        print("Number of images in the loaded training dataset:", len(loaded_dataset["trainset"]))
        print("Number of images in the loaded testing dataset:", len(loaded_dataset["testset"]))
        dir = self.root_directory + "/datasets/"
        base_io.save_file(dir,dataset_name+"_training",loaded_dataset["trainset"])
        base_io.save_file(dir,dataset_name+"_testing",loaded_dataset["testset"])
        
    def get_model(self):
        return 0
    
    def get_data(self):
        return 0
    
    def _execute_on_msg(self, header_parts, body):

        if header_parts[2] == 'collect_logic_model':
            print("received collect model command. parsing command ...")
            model_params = body.split(' -model_params ')[1].split(';')[0]
            self.collect_logic_model(model_params)

        if header_parts[2] == 'construct_logic_model':
            print("received construct model command. parsing command ...")
            id = body.split('-id ')[1].split(' -model_name ')[0]
            if(id == 'all' or id == self.id):
                model_name = body.split('-model_name ')[1].split(' -model_params ')[0]
                model_params = body.split(' -model_params ')[1].split(';')[0]
            
                self.construct_logic_model(model_name, model_params)
               
        
        if header_parts[2] == 'collect_logic_data':
            print("received collect data command. parsing command ...")
            id = body.split('-id ')[1].split(' -dataset_name ')[0]
            print(id)
            print(self.id)
            if(id == 'all' or id == self.id):
                print("id match")
                dataset_name = body.split('-dataset_name ')[1].split(' -dataset_type ')[0]
                dataset_type = body.split(' -dataset_type ')[1].split(' -data ')[0]
                bin_data     = body.split(' -data ')[1].split(';')[0]
                self.collect_logic_data(dataset_name,dataset_type,bin_data)
        
        if header_parts[2] == 'load_model':
            model_name = body.split('-model_name ')[1].split(';')[0]
            self.load_model(model_name)

        if header_parts[2] == 'load_dataset':
            dataset_name = body.split('-dataset_name ')[1].split(';')[0]
            self.load_dataset(dataset_name)


        if header_parts[2] == 'client_update' :
                
            if(self.trainer.is_trainer):
                num_epochs = body.split(' -num_epochs ')[1].split(' -batch_size ')[0]
                batch_size = body.split(' -batch_size ')[1].split(';')[0]

                tracemalloc.start()
                # tracemalloc.reset_peak()
                updated_model = self.trainer.client_update( self.client_logic.simulated_logic_data_train,
                                                            self.client_logic.logic_model,
                                                            int(num_epochs),
                                                            int(batch_size),
                                                            round = 1)
                
                mem_usage = tracemalloc.get_traced_memory()[0]
                tracemalloc.stop()

                self.client_logic.logic_model = updated_model
                print("Local model updated.")
                self.publish(self.ClTCoT,"local_training_complete" , " -id " + str(self.id) + " -mem " + str(mem_usage)) #ADD RAM USAGE
    
        if header_parts[2] == 'send_local' : 
            id = body.split('-id ')[1].split(';')[0]

            ##TODO: Associate the following block of code to the dflmq_client so that the client code receives the model and the id, while processing the id, will determine whether to send the local model or not.
            if(self.trainer.is_trainer):
                if(id == "all" or id == self.id):
                        if(self.aggregator.is_aggregator == False):       
                            self.send_local()
                        else:
                            print("No need to send locals, client is aggregator. Informing coordinator.")
                            self.publish(self.ClTCoT,"aggregator_received_local_params"," -id " + self.id)
                else:
                    print("can't send local model params because client is not a trainer!")

            
        