from . import components as components
from .components import Cluster
from .components import Cluster_Node
from .components import Session
from .optimizers.PSO_placement import *

import random
import numpy as np
class Load_Balancer():
    def __init__(self):
        self.optimizers = {}
        self.role_vector_size = {}

    def random_initialize_roles(self,session, optimizer = "random"):
        #TODO: Look into the list of nodes, and the list of clients, and associate the clients to the roles.
        #For the assignment, the input argument to the set_roles should be built, which is the role_vector.
        #Based on the policy, the assigments can varry. The basic policy is that a client who has agreed to be aggregator should be assigned to agg or agg_t nodes.
        role_vector_counter = 0
        init_role_vector = np.zeros(len(session.role_vector),dtype=int)
        while(True):
            client_index = random.randint(0,len(session.client_list)-1)
            # print(client_index)
            if(client_index in init_role_vector):
                continue
            # print("number of added clients: " + str(len(session.client_list)))
            if(session.client_list[client_index].preferred_role == "trainer"):
                continue
            else:
                print(len(init_role_vector))
                init_role_vector[role_vector_counter] = client_index
                role_vector_counter += 1
            if(role_vector_counter == len(init_role_vector)):
                break
        session.role_vector = init_role_vector
        self.role_vector_size[session.session_id] = len(session.role_vector)

        return session.role_vector
    

    def pso_initialize_roles(self,session,particle_num):
       
        rand_poses = []
        for i in range(particle_num):
            role_vector_counter = 0
            new_role_vec = np.zeros(len(session.role_vector),dtype=int)
            while(True):
                client_index = random.randint(0,len(session.client_list)-1)
                # print(client_index)
                if(client_index in new_role_vec):
                    continue
                # print("number of added clients: " + str(len(session.client_list)))
                if(session.client_list[client_index].preferred_role == "trainer"):
                    continue
                else:
                    print(len(new_role_vec))
                    new_role_vec[role_vector_counter] = client_index
                    role_vector_counter += 1
                if(role_vector_counter == len(new_role_vec)):
                    break
            
            rand_poses.append(new_role_vec)
        
        self.optimizers[session.session_id] = PSO(particle_num,len(rand_poses[0]),len(session.client_list),rand_poses)

        session.role_vector =  self.optimizers[session.session_id].get_next_particle()
        self.role_vector_size[session.session_id] = len(session.role_vector)
        return session.role_vector
    
    def greedy_optimize_roles(self,session):
        #TODO: Read the calculated cost of FL in the previous round, and accordingly build a new role_vector, and feed it to the update_roles.
        session.update_roles([])
        return []
    
    def randomly_update_roles(self,session):
        #TODO: Read the calculated cost of FL in the previous round, and accordingly build a new role_vector, and feed it to the update_roles.
        role_vector_counter = 0
        init_role_vector = np.zeros(len(session.role_vector),dtype=int)
        while(True):
            client_index = random.randint(0,len(session.client_list)-1)
            if(client_index in init_role_vector):
                continue
            if(session.client_list[client_index].preferred_role == "trainer"):
                continue
            else:
                init_role_vector[role_vector_counter] = client_index
                role_vector_counter += 1
            if(role_vector_counter == len(init_role_vector)):
                break
            
        session.update_roles(init_role_vector)
        return session.role_vector

    def uniformly_update_roles(self,session):
        #TODO: Read the calculated cost of FL in the previous round, and accordingly build a new role_vector, and feed it to the update_roles.
        session.update_roles([])
        return []
    
    def pso_optimize_roles(self,session,round_processing_delay):
        #TODO: Read the calculated cost of FL in the previous round, and accordingly build a new role_vector, and feed it to the update_roles.
        
        self.optimizers[session.session_id].optimize(round_processing_delay)
        new_suggested_role_vector = self.optimizers[session.session_id].get_next_particle()
        session.update_roles(new_suggested_role_vector)

        return new_suggested_role_vector

    
