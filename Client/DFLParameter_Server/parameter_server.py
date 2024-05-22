import torch
import torch.nn as nn
from custom_models import VGG
from custom_datasets import CIFAR10
import json

from executable_class import PubSub_Base_Executable

class dflmq_parameter_server(PubSub_Base_Executable):
    
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
       
        self.CoTPST = "Coo_to_PS_T"
        self.PSTCoT = "PS_to_Coo_T"
        self.PSTCliT = "PS_to_Cli_T"
        self.executables.append('broadcast_model')
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        self.model_name = 'VGG11'
        self.global_model   =  VGG(self.model_name)
        self.dataset        = CIFAR10()

        self.client.subscribe(self.CoTPST)

    def _get_header_body(self , msg) -> list :
        header_body = str(msg.payload.decode()).split('::')
        print("MESSAGE Header: " + header_body[0])
        header_parts = header_body[0].split('|')
        return header_parts

    def _execute_on_msg(self,msg):
        header_parts = self._get_header_body(msg)

        if header_parts[2] == 'broadcast_model' : 
            self.broadcast_model()
            
    def execute_on_msg(self, client, userdata, msg) -> None :
        
        super().execute_on_msg(client, userdata, msg)
        self._execute_on_msg(msg)
        
    def broadcast_model(self):
        weights_and_biases = {}
        for name, param in self.global_model.named_parameters():
            weights_and_biases[name] = param.data.tolist()

        model_params = json.dumps(weights_and_biases)
        print(len(model_params))
        self.publish(self.PSTCliT,"collect_logic_model"," -id all -model_name " + str(self.model_name)+ " -model_params " + str(model_params)) 
        


userID = input("Parameter Server ID: ")
print("PS with ID=" + userID +" is created.")

exec_program = dflmq_parameter_server(myID = userID,
        broker_ip = 'localhost' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)
exec_program.base_loop()



#For image conversion to Json and back:

#________TO JSON::
# import json
# import base64

# def image_to_base64(image_path):
#     with open(image_path, "rb") as img_file:
#         return base64.b64encode(img_file.read()).decode('utf-8')

# def images_to_json(image_paths):
#     image_data = []
#     for path in image_paths:
#         image_data.append({
#             "filename": path.split("/")[-1],
#             "data": image_to_base64(path)
#         })
#     return json.dumps(image_data)

# # Example usage
# image_paths = ["image1.jpg", "image2.png", "image3.gif"]  # Paths to your images
# json_string = images_to_json(image_paths)
# print(json_string)


#________TO IMG::
# from PIL import Image
# from io import BytesIO

# def base64_to_image(base64_string, filename):
#     image_data = base64.b64decode(base64_string)
#     with open(filename, "wb") as img_file:
#         img_file.write(image_data)

# def json_to_images(json_string):
#     image_data = json.loads(json_string)
#     for data in image_data:
#         base64_to_image(data['data'], data['filename'])

# # Example usage
# json_string = '...'  # Your JSON string containing image data
# json_to_images(json_string)
