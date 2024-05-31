
import numpy as np
import torch, torchvision
import torch
import torchvision
import torchvision.transforms as transforms

from torchvision import datasets, transforms
from torch.utils.data.dataset import Dataset   
torch.backends.cudnn.benchmark=True


class CIFAR10():
    
    def __init__(self) -> None:
        self.batch_size = 32


    def load_data_for_clients(self, num_clients):
        
        transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),])
        # transform = transforms.Compose([transforms.ToTensor()])

        # Loading CIFAR10 using torchvision.datasets
        traindata = datasets.CIFAR10('./data', train=True, download=True,
                            transform= transform_train)

        print("size of training dataset in total: " + str(len(traindata)))

        # Dividing the training data into num_clients, with each client having equal number of images
        traindata_split = torch.utils.data.random_split(traindata, [int(traindata.data.shape[0] / num_clients) for _ in range(num_clients)])


        print("size of each training sub-dataset: " + str(len(traindata_split[0])))
        # Creating a pytorch loader for a Deep Learning model
        #train_loader = [torch.utils.data.DataLoader(x, batch_size=batch_size, shuffle=True) for x in traindata_split]

        # Normalizing the test images
        transform_test = transforms.Compose([
            #transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])

        # Loading the test iamges and thus converting them into a test_loader
        #test_loader = torch.utils.data.DataLoader(datasets.CIFAR10('./data', train=False, transform=transform_test), batch_size=batch_size, shuffle=True)
        testdata = datasets.CIFAR10('./data', train=False, transform=transform_test)
        return [traindata_split, testdata]


class MNIST():
    def __init__(self) -> None:
        self.batch_size = 32
    
    def load_data_for_clients(self,num_clients):
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
        train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
        test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

        train_dataset_split = torch.utils.data.random_split(train_dataset, [int(train_dataset.data.shape[0] / num_clients) for _ in range(num_clients)])
        return (train_dataset_split,test_dataset)
        # train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=len(train_dataset), shuffle=True)
        # test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=10000, shuffle=True)

        # x_train, y_train = next(iter(train_loader))
        # x_test, y_test = next(iter(test_loader))