import json
import torch
import torch.nn as nn

def get_pytorch_model_info(model):
    """
    Extract architectural details of a PyTorch model.
    """
    model_info = []

    for name, layer in model.named_children():  # Iterate only through direct child layers
        layer_info = {
            "layer_name": name,
            "layer_type": layer.__class__.__name__,
            "num_parameters": sum(p.numel() for p in layer.parameters() if p.requires_grad),
        }

        model_info.append(layer_info)

    return model_info


def model_to_json(model):
    """
    Convert PyTorch model architecture to JSON format.
    """
    model_info = get_pytorch_model_info(model)
    return json.dumps(model_info, indent=4)


# Example PyTorch Model
class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(10, 20)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(20, 5)

    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))

# Create model instance
pytorch_model = SimpleNN()

# Convert to JSON and print
pytorch_json = model_to_json(pytorch_model)
print(pytorch_json)
