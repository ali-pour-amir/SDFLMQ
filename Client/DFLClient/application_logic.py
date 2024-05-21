from custom_models import VGG
import json
import torch

class dflmq_client_app_logic():
    
    def __init__(self, is_simulating)-> None:

        self.is_simulating = is_simulating
        self.logic_model = None
        self.simulated_logic_data = None
        
        self.executables = ['construct_logic_model', 'collect_logic_model', 'collect_logic_data']

    def construct_logic_model(self, model_name):
        self.logic_model = VGG(model_name)
    
    def collect_logic_model(self, parameters):
        weights_and_biases = json.loads(parameters)
        for name, param in self.logic_model.named_parameters():
            if name in weights_and_biases:
                param.data = torch.tensor(weights_and_biases[name])
    
    def collect_logic_data(self,data_batch):
        return 0

    def get_model(self):
        return 0
    
    def get_data(self):
        return 0

    def _execute_on_msg(self, msg,_get_header_body_func):
        header_parts = _get_header_body_func(msg)
        header_body = str(msg.payload.decode()).split('::')
        
        if header_parts[2] == 'collect_logic_model':
            id = header_body[1].split('-id ')[1].split(' -model_name ')[0]
            model_name = header_body[1].split('-model_name ')[1].split(' -model_params ')[0]
            model_params = json.loads(header_body[1].split(' -model_params ')[1].split(';')[0])
            
            self.construct_logic_model(model_name)
            self.collect_logic_model(model_params)