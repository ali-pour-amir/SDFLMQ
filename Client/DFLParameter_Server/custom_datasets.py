
import numpy as np
import torch, torchvision

from torchvision import datasets, transforms
from torch.utils.data.dataset import Dataset   
torch.backends.cudnn.benchmark=True


class CIFAR10():
    
    def __init__(self) -> None:
        self.batch_size = 32


    def load_data_for_clients(self, num_clients,batch_size):
        
        transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),])

        # Loading CIFAR10 using torchvision.datasets
        traindata = datasets.CIFAR10('./data', train=True, download=True,
                            transform= transform_train)

        # Dividing the training data into num_clients, with each client having equal number of images
        traindata_split = torch.utils.data.random_split(traindata, [int(traindata.data.shape[0] / num_clients) for _ in range(num_clients)])

        # Creating a pytorch loader for a Deep Learning model
        train_loader = [torch.utils.data.DataLoader(x, batch_size=batch_size, shuffle=True) for x in traindata_split]

        # Normalizing the test images
        transform_test = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])

        # Loading the test iamges and thus converting them into a test_loader
        test_loader = torch.utils.data.DataLoader(datasets.CIFAR10('./data', train=False, transform=transform_test), batch_size=batch_size, shuffle=True)

        return [train_loader, test_loader]
