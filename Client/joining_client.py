import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from Core.sdflmq_client_logic import SDFLMQ_Client
import random
import time
from datetime import datetime, timedelta
myid = "client_" + str(random.randint(0,10000))


    
def printsomething():
    print("Model update received")

fl_client = SDFLMQ_Client(  myID=myid,
                            broker_ip = 'localhost',
                            broker_port = 1883,
                            preferred_role="trainer",
                            loop_forever=False)

fl_client.join_fl_session(session_id="session_01",
                            memcap=0,
                            model_spec=0,
                            fl_rounds=10,
                            model_name="mlp",
                            modelsize=1000,
                            preferred_role="aggregator",
                            processing_speed= 10,
                            model_update_callback=printsomething)















LOOPING = True
while(LOOPING):
    fl_client.oneshot_loop()
    time.sleep(1)