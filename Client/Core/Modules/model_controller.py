import json
import numpy


class Model_Controller():
    def __init__(self,client_id):
        self.client_id = client_id
        self.Models = {}

    def get_model(self,session_id):
        return self.Models[session_id]
    
    def set_model(self, session_id,model):
        self.Models[session_id] = model

    def get_model_spec(self,model):
        return 0
    
    
