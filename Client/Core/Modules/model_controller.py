import json
import numpy
import torch
import torch.nn as nn

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
    
    def get_model_spec(self,model,ml_framework = "pytorch"):
        if(ml_framework == "pytorch"):
            model_info = self.get_pytorch_model_info(model)
            return json.dumps(model_info, indent=4)
        return ""
    
    def get_pytorch_model_info(self,model):
        model_info = []
        for name, layer in model.named_children():  # Iterate only through direct child layers
            layer_info = {
                "layer_name": name,
                "layer_type": layer.__class__.__name__,
                "num_parameters": sum(p.numel() for p in layer.parameters() if p.requires_grad),
            }
            model_info.append(layer_info)

        return model_info

