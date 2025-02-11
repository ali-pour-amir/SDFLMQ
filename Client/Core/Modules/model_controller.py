import json
import numpy
import torch


class Model_Controller():
    def __init__(self,client_id):
        self.client_id = client_id
        self.Models = {}

    def get_model(self,session_id):
        return self.Models[session_id]
    
    def set_model(self, session_id,model):
        self.Models[session_id] = model

    def update_model(self,session_id,model_params):
        self.Models[session_id].load_state_dict(model_params)
    
    def get_model_spec(self,model):
        return 0 #TODO: Complete logic
    
    
