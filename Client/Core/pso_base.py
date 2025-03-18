from measurements.tools.display_output import *
from measurements.tools.store_output import *
from random import randint , random , sample , seed 
from os import system
import copy 

# Points:
# 1- when we increase the population, we should also proportionally increase the c1. otherwise we will see fluctuation, plus not having particles converging to a global best.
# For instnace, if I choose pop_n = 3, then I will go wiht c1 = 0.01. If I choose c1 = 0.1 then it will show fluctuation and sometimes no convergence in the maximum total processing delay plot (check it with seed = 3).
# But when I increase the pop_n, for instance to 10, then if I keep c1 to 0.01, I would still see convergence, but if I slightly increase c1 to higher value, such as 0.1, then I will not only see convergence, but also a lower final value for the total processing delay to converge to.
# And if I increase c1 to for instance 0.2, then I will see again that there is more fluctuation, and no convergence.
# 2- iw in our case needs to be kept at lower value. I tried with an adaptive iw which would decrease over time, but it is sometime effective, someitmes not. I would not keep the adaptive mode on. so far, I tried 0.1, 0.01, and 0.001.
# 3- Trying with lower particle numbers in our case seems reasonable and so far promissing. It processes faster, and converges faster. But noting that once we go low on the population number, such as pop_n = 3, then we have to keep c1 to 0.01

# Global parameters
# PSO parameters                            
iw = .01                                     # Inertia Weight (Higher => Exploration | Lower => Exploitation)   (0.1 , 0.5)
c1 = .01                                     # Pbest coefficient (0.01 , 0.1)
c2 = 1                                       # Gbest coefficient 
pop_n = 10                                    # Population number (3 , 5 , 10 , 15 , 20*)
max_iter = 100                               # Maximum iteration

# System parameters
DEPTH = 5
WIDTH = 4
dimensions = 0 if DEPTH <= 0 or WIDTH <= 0 else sum(WIDTH**i for i in range(DEPTH))   
Client_list = []
Role_buffer = []
Role_dictionary = {}
randomness_seed = 10
tracking_mode = True   
velocity_factor = 0.1                       # Increasing velocity_factor causes more exploration resulting higher fluctuations in the particles plot (default range between 0 and 1 (Guess))

# Experiment parameters
stepper = 1
scenario_file_number = WIDTH // stepper
scenario_folder_number = DEPTH - 1                       
scenario_folder_name = f"scenario_case_{scenario_folder_number}"

# Graph illustration required parameters 
particles_fitness_fig_path = f"./measurements/results/{scenario_folder_name}/particles_fitness_{scenario_file_number}.pdf"
swarm_best_fitness_fig_path = f"./measurements/results/{scenario_folder_name}/swarm_best_fitness_{scenario_file_number}.pdf"
tpd_fig_path = f"./measurements/results/{scenario_folder_name}/tpd_{scenario_file_number}.pdf"

sbpfl = ("iteration" , "best particle fitness")
pfl = ("iteration" , "particles fitness") 
tpdl = ("iteration" , "total processing delay")

sbpft = "Swarm’s Best Particle Fitness Plot"
pft = "Particles Fitness Plot"
tpdt = "Total Processing Delay Plot"

gbest_particle_fitness_results = []
particles_fitnesses_buffer = []
particles_fitnesses_tuples = []

tpd_buffer = []
tpd_tuples = []
iterations = []

# CSV output required parameters
csv_particles_output_file_name = f"particles_data_{scenario_file_number}"
csv_swarm_best_output_file_name = f"swarm_best_data_{scenario_file_number}"
csv_tpd_output_file_name = f"tpd_data_{scenario_file_number}"

csv_particles_data_path = f"./measurements/results/{scenario_folder_name}/{csv_particles_output_file_name}.csv"
csv_swarm_best_data_path = f"./measurements/results/{scenario_folder_name}/{csv_swarm_best_output_file_name}.csv"
csv_tpd_data_path = f"./measurements/results/{scenario_folder_name}/{csv_tpd_output_file_name}.csv"

particles_columns = ["iteration"] + [f"particle_{i+1}_fitness" for i in range(pop_n)]
swarm_best_columns = ["iteration", "swarm_best_fitness"]
tpd_columns = ["iteration"] + [f"tpd_particle_{i+1}" for i in range(pop_n)]

csv_cols = [particles_columns, swarm_best_columns, tpd_columns]
csv_rows = [[], [], []]

# JSON output required parameters (Particles constant metadata)
json_path = f"./measurements/results/{scenario_folder_name}/pso_scenario_case_{scenario_file_number}.json"
json_pso_dict = {
    "DEPTH" : DEPTH,
    "WIDTH" : WIDTH,
    "dimensions" : dimensions,
    "randomness_seed" : randomness_seed,
    "iw" : iw,
    "c1" : c1,
    "c2" : c2,
    "pop_n" : pop_n,
    "max_iter" : max_iter,
    "velocity_factor" : velocity_factor
} 

# Particle class
class Particle :
    def __init__(self, pos , fitness , velocity , best_pos_fitness) : 
        self.pos = pos
        self.fitness = fitness
        self.velocity = velocity
        self.best_pos = self.pos.copy()
        self.best_pos_fitness = best_pos_fitness

# Swarm class
class Swarm : 
    def __init__(self , pop_n , dimensions , root) :
        self.particles = self.__generate_random_particles(pop_n , dimensions , root)
        self.global_best_particle = copy.deepcopy(max(self.particles, key=lambda particle: particle.fitness))

    def __generate_random_particles(self, pop_n, dimensions , root):
        init_particle_pos = [client.client_id for client in Client_list if client.is_aggregator]
        cll = len(Client_list)
        particles = []

        for i in range(pop_n):
            if i != 0 : 
                particle_pos = sample(range(cll), dimensions)
                root = reArrangeHierarchy(particle_pos)  

            else : 
                particle_pos = init_particle_pos

            fitness, _ , _ = processing_fitness(root)
            velocity = [0 for _ in range(dimensions)]       
            best_pos_fitness = fitness                   
            particles.append(Particle(particle_pos, fitness, velocity, best_pos_fitness))

        return particles
        
class Client :
    def __init__(self, memcap, mdatasize, client_id , label , pspeed , is_aggregator=False) :
        self.memcap = memcap 
        self.mdatasize = mdatasize
        self.label = label 
        self.pspeed = pspeed
        self.is_aggregator = is_aggregator
        self.client_id = client_id  
        self.processing_buffer = []
        self.memscore = 0

    def changeRole(self , new_pos) :         # This function traverses the Client_list to find the client with equal client_id then it first buffers the role of the client if the role is trainer, and then associates the new_role_label to the selected client 
        if not self.is_aggregator : 
            Role_buffer.append(self.label) 
        self.processing_buffer = []
        self.label = list(Role_dictionary.keys())[new_pos]
        self.is_aggregator = True
    
    def takeAwayRole(self) :                 # This function traverses the Client_list and checks for the client that has the selected role in the arguments then it nulls the label and the processing_buffer   
        self.label = None
        self.processing_buffer = []  


# Fitness function
def processing_fitness(master):
    bft_queue = [master]                     # Start with the root node
    levels = []                              # List to store nodes level by level
    total_process_delay = 0
    total_memscore = 0 

    # Perform BFT to group nodes by levels
    while bft_queue:
        level_size = len(bft_queue)
        current_level = []

        for _ in range(level_size):
            current_node = bft_queue.pop(0)
            current_level.append(current_node)

            if current_node.is_aggregator :
                bft_queue.extend(current_node.processing_buffer)  

        levels.append(current_level)  

    levels.reverse()

    # Calculate delays level by level
    for level in levels:
        cluster_delays = []  

        for node in level:
            if node.is_aggregator :

                # Update the node's mdatasize with its children's cumulative memory size
                cluster_head_memcons = node.mdatasize + sum(
                    child.mdatasize for child in node.processing_buffer
                )
                
                node.memscore = node.memcap - cluster_head_memcons
                total_memscore += node.memscore
                cluster_delay = cluster_head_memcons / node.pspeed
                cluster_delays.append(cluster_delay)

                # Print details for the cluster
                # print(f"AgTrainer: {node.label}, MDataSize: {node.mdatasize} Memory Consumption : {cluster_head_memcons}, Cluster Head Delay: {cluster_delay:.2f}")
                
                # for child in node.processing_buffer:
                    # print(f"Trainer: {child.label}, MDataSize: {child.mdatasize}")

        # Find the maximum cluster delay for the level
        if cluster_delays:
            max_cluster_delay = max(cluster_delays)
            total_process_delay += max_cluster_delay  # Add max delay of the level to the total delay
            # print(f"Level Max Cluster Delay: {max_cluster_delay:.2f}\n")

    # print(f"Total Processing Delay: {total_process_delay:.2f}")
    # print(f"Total Memory Score: {total_memscore}")
    
    return -total_process_delay  , total_process_delay , total_memscore

def generate_hierarchy(depth, width):
    level_agtrainer_list = []
    agtrainer_list = []
    trainer_list = []

    def create_agtrainer(label_prefix, level):
        pspeed = randint(5, 15)
        memcap = randint(10, 50)
        mdatasize = 5                         # in the beginning it's a fixed value but in the future as a stretch goal we can have variable MDataSize due to quantization and knowledge distillation techniques
        length = len(Client_list) 
        new_client = Client(memcap, mdatasize, length, f"t{label_prefix}ag{level}", pspeed, True)
        Client_list.append(new_client)
        agtrainer_list.append(new_client)
        level_agtrainer_list.append(new_client)
        return new_client

    def create_trainer(label_prefix):
        pspeed = randint(5, 15)
        memcap = randint(10, 50)
        mdatasize = 5 
        length = len(Client_list)
        new_client = Client(memcap, mdatasize, length, label_prefix , pspeed)
        Client_list.append(new_client)
        trainer_list.append(new_client)
        return new_client

    root = create_agtrainer(0, 0)
    current_level = [root]
    level_agtrainer_list = []

    for d in range(1, depth):
        next_level = []
        for parent in current_level:
            for _ in range(width):
                child = create_agtrainer(len(level_agtrainer_list), d)
                parent.processing_buffer.append(child)
                next_level.append(child)

                for role in [parent , child] :
                    Role_dictionary[role.label] = [child.label for child in role.processing_buffer]

        if d == depth - 1:    
            for client in level_agtrainer_list :
                for j in range(2):          
                    trainer = create_trainer(f"{client.label}_{j+1}")
                    client.processing_buffer.append(trainer)

                for role in [client , trainer] :
                    Role_dictionary[role.label] = [child.label for child in role.processing_buffer]

        level_agtrainer_list = []
        current_level = next_level

    return root

def printTree(node, level=0, is_last=True, prefix=""):
    connector = "└── " if is_last else "├── "
    if node.is_aggregator : 
        print(f"{prefix}{connector}{node.label} (MemCap: {node.memcap}, MDataSize: {node.mdatasize} Pspeed: {node.pspeed}, ID: {node.client_id}, MemScore: {node.memscore})")

    elif node.is_aggregator == False :
        print(f"{prefix}{connector}{node.label} (MemCap: {node.memcap}, MDataSize: {node.mdatasize}, ID: {node.client_id}, MemScore: {node.memscore})")

    if node.is_aggregator :
        for i, child in enumerate(node.processing_buffer):
            new_prefix = prefix + ("    " if is_last else "│   ")
            printTree(child, level + 1, i == len(node.processing_buffer) - 1, new_prefix)

def changeRole(client , new_pos) :                # This function traverses the Client_list to find the client with equal client_id then it first buffers the role of the client if the role is trainer, and then associates the new_role_label to the selected client 
    if not client.is_aggregator : 
        Role_buffer.append(client.label) 
    client.processing_buffer = []
    client.label = list(Role_dictionary.keys())[new_pos]
    client.is_aggregator = True
    
def takeAwayRole(client) :                        # This function traverses the Client_list and checks for the client that has the selected role in the arguments then it nulls the label and the processing_buffer   
    client.label = None
    client.processing_buffer = []   

def reArrangeHierarchy(pso_particle) :            # This function has the iterative approach to perform change role and take away role
    for new_pos , clid in enumerate(pso_particle) : 
        for client in Client_list : 
            if client.label == list(Role_dictionary.keys())[new_pos] :
                client.takeAwayRole()

            if client.client_id == clid : 
                client.changeRole(new_pos)
                
            client.memscore = 0
            
    for client in Client_list : 
        if client.label == None :
            client.label = Role_buffer.pop()    
            client.is_aggregator = False 
    
        if client.is_aggregator : 
            if len(client.processing_buffer) == 0 : 
                temp = Role_dictionary[client.label]
                for role in temp : 
                    for c in Client_list :
                        if  c.label == role : 
                            client.processing_buffer.append(c) 
                        
    for client in Client_list :
        if client.label == list(Role_dictionary.keys())[0] :
            return client

def updateVelocity(current_velocity, current_position, personal_best, global_best, iw, c1, c2):
    r1 = [random() for _ in range(len(current_velocity))]
    r2 = [random() for _ in range(len(current_velocity))]

    inertia = [iw * v for v in current_velocity]
    cognitive = [c1 * r1[i] * (personal_best[i] - current_position[i]) for i in range(len(current_velocity))]
    social = [c2 * r2[i] * (global_best[i] - current_position[i]) for i in range(len(current_velocity))]
    
    max_velocity = max(1, int(len(current_velocity) * velocity_factor))
    new_velocity = [round(inertia[i] + cognitive[i] + social[i]) for i in range(len(current_velocity))]
    new_velocity = [max(min(v, max_velocity), -max_velocity) for v in new_velocity]  # Apply velocity limits

    return new_velocity

def applyVelocity(p_position, p_velocity):
    new_position = []
    client_count = len(p_position)

    for a, b in zip(p_position, p_velocity):
        np = (a + b) % client_count  

        while np in new_position:
            np = (np + 1) % client_count  

        new_position.append(np)

    return new_position

def PSO_FL_SIM() :    
    global iw

    if tracking_mode : 
        seed(randomness_seed)

    root = generate_hierarchy(DEPTH , WIDTH)

    counter = 1

    swarm = Swarm(pop_n , dimensions , root)

    while counter <= max_iter: 
        for particle in swarm.particles :
            particles_fitnesses_buffer.append(particle.fitness)

            new_velocity = updateVelocity(particle.velocity, particle.pos, particle.best_pos, swarm.global_best_particle.best_pos, iw, c1, c2)
            new_position = applyVelocity(particle.pos, new_velocity)
            root = reArrangeHierarchy(new_position)

            new_pos_fitness, tp, ـ = processing_fitness(root)
            particle.pos = new_position
            particle.fitness = new_pos_fitness
            particle.velocity = new_velocity
            
            if particle.fitness > particle.best_pos_fitness :  
                particle.best_pos = particle.pos.copy()
                particle.best_pos_fitness = copy.copy(particle.fitness)

                if particle.fitness > swarm.global_best_particle.fitness:
                    swarm.global_best_particle = copy.deepcopy(particle)              
            
            tpd_buffer.append(tp)

        # iw = 0.15 - ((0.14 * counter) / max_iter) 

        iterations.append(counter)
        
        gbest_particle_fitness_results.append(swarm.global_best_particle.fitness)
        tpd_tuples.append(tpd_buffer.copy())
        particles_fitnesses_tuples.append(particles_fitnesses_buffer.copy()) # We could simply reverse the TPD plot and get Particles Fitnesses Plot but as the fitness function might change later this method is not reliable 
        
        particles_row = [counter] + [round(fitness , 2) for fitness in particles_fitnesses_buffer]
        csv_rows[0].append(particles_row)
        
        swarm_best_row = [counter, round(swarm.global_best_particle.fitness , 2)]
        csv_rows[1].append(swarm_best_row)
        
        tpd_row = [counter] + [round(tpd , 2) for tpd in tpd_buffer]
        csv_rows[2].append(tpd_row)


        system("clear")
        print(len(Client_list))
        print("Iteration : " , counter)
        
        tpd_buffer.clear()
        particles_fitnesses_buffer.clear()
        
        counter += 1

    save_data_to_csv(csv_cols[0] , csv_rows[0] , csv_particles_data_path)
    save_data_to_csv(csv_cols[1] , csv_rows[1] , csv_swarm_best_data_path)
    save_data_to_csv(csv_cols[2] , csv_rows[2] , csv_tpd_data_path)
    save_metadata_to_json(json_pso_dict , json_path)

    illustrate_plot(gbest_particle_fitness_results , sbpfl , sbpft , swarm_best_fitness_fig_path)
    plot_tuple_curves(particles_fitnesses_tuples , pfl , pft , particles_fitness_fig_path)
    plot_tuple_curves(tpd_tuples , tpdl , tpdt , tpd_fig_path)
    

if __name__ == "__main__" : 
    PSO_FL_SIM()
