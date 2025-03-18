
from random import randint , random , sample , seed 
from os import system
import copy 


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
    def __init__(self , pop_n , particle_size, num_clients, random_poses = []) :
        
        self.particles = self.__generate_random_particles(pop_n , particle_size,num_clients)
        for i in range(len(random_poses)):
            self.particles[i].pos = random_poses[i]
            self.particles[i].best_pos = random_poses[i]
            
        # self.global_best_particle = copy.deepcopy(max(self.particles, key=lambda particle: particle.fitness))
        self.global_best_particle = copy.deepcopy(self.particles[0])

    def __generate_random_particles(self, pop_n, particle_size, num_clients):
        init_particle_pos = [randint(0,num_clients) for _ in range(particle_size)]
        particles = []

        for i in range(pop_n):
            particle_pos = init_particle_pos
            fitness = None
            velocity = [0 for _ in range(particle_size)]       
            best_pos_fitness = None                   
            particles.append(Particle(particle_pos, fitness, velocity, best_pos_fitness))

        return particles


class PSO:
    def __init__(self, particle_num, particle_size, num_clients, random_poses):

        self.iw = .01                                     # Inertia Weight (Higher => Exploration | Lower => Exploitation)   (0.1 , 0.5)
        self.c1 = .01                                     # Pbest coefficient (0.01 , 0.1)
        self.c2 = 1                                       # Gbest coefficient 
        self.pop_n = 10                                    # Population number (3 , 5 , 10 , 15 , 20*)
        self.max_iter = 100  
        self.particle_size = particle_size

        # System parameters
        self.randomness_seed = 10
        self.tracking_mode = True   
        self.velocity_factor = 0.1                       # Increasing velocity_factor causes more exploration resulting higher fluctuations in the particles plot (default range between 0 and 1 (Guess))

        self.particle_counter = -1
        self.iter_counter = -1

        self.swarm = Swarm(self.pop_n , self.particle_size,num_clients,random_poses)
        # if self.tracking_mode : 
        #     seed(self.randomness_seed)

        
        # Experiment parameters
        # stepper = 1
        # scenario_file_number = randint(1,1000)
        # scenario_folder_number = randint(1,1000)                       
        # scenario_folder_name = f"scenario_case_{scenario_folder_number}"

        # # Graph illustration required parameters 
        # particles_fitness_fig_path = f"./measurements/results/{scenario_folder_name}/particles_fitness_{scenario_file_number}.pdf"
        # swarm_best_fitness_fig_path = f"./measurements/results/{scenario_folder_name}/swarm_best_fitness_{scenario_file_number}.pdf"
        # tpd_fig_path = f"./measurements/results/{scenario_folder_name}/tpd_{scenario_file_number}.pdf"

        # sbpfl = ("iteration" , "best particle fitness")
        # pfl = ("iteration" , "particles fitness") 
        # tpdl = ("iteration" , "total processing delay")

        # sbpft = "Swarm’s Best Particle Fitness Plot"
        # pft = "Particles Fitness Plot"
        # tpdt = "Total Processing Delay Plot"

        self.gbest_particle_fitness_results = []
        self.particles_fitnesses_buffer = []
        self.particles_fitnesses_tuples = []

        self.tpd_buffer = []
        self.tpd_tuples = []
        self.iterations = []

        # # CSV output required parameters
        # csv_particles_output_file_name = f"particles_data_{scenario_file_number}"
        # csv_swarm_best_output_file_name = f"swarm_best_data_{scenario_file_number}"
        # csv_tpd_output_file_name = f"tpd_data_{scenario_file_number}"

        # csv_particles_data_path = f"./measurements/results/{scenario_folder_name}/{csv_particles_output_file_name}.csv"
        # csv_swarm_best_data_path = f"./measurements/results/{scenario_folder_name}/{csv_swarm_best_output_file_name}.csv"
        # csv_tpd_data_path = f"./measurements/results/{scenario_folder_name}/{csv_tpd_output_file_name}.csv"

        # particles_columns = ["iteration"] + [f"particle_{i+1}_fitness" for i in range(pop_n)]
        # swarm_best_columns = ["iteration", "swarm_best_fitness"]
        # tpd_columns = ["iteration"] + [f"tpd_particle_{i+1}" for i in range(pop_n)]

        # csv_cols = [particles_columns, swarm_best_columns, tpd_columns]
        # csv_rows = [[], [], []]

        # JSON output required parameters (Particles constant metadata)
        # json_path = f"./measurements/results/{scenario_folder_name}/pso_scenario_case_{scenario_file_number}.json"
        # json_pso_dict = {
        #     "DEPTH" : DEPTH,
        #     "WIDTH" : WIDTH,
        #     "dimensions" : dimensions,
        #     "randomness_seed" : randomness_seed,
        #     "iw" : iw,
        #     "c1" : c1,
        #     "c2" : c2,
        #     "pop_n" : pop_n,
        #     "max_iter" : max_iter,
        #     "velocity_factor" : velocity_factor
        # } 


    # Fitness function
    def processing_fitness(self,tpd):
        return -1 * float(tpd)

    def updateVelocity(self,current_velocity, current_position, personal_best, global_best, iw, c1, c2):
        r1 = [random() for _ in range(len(current_velocity))]
        r2 = [random() for _ in range(len(current_velocity))]

        inertia = [iw * v for v in current_velocity]
        cognitive = [c1 * r1[i] * (personal_best[i] - current_position[i]) for i in range(len(current_velocity))]
        social = [c2 * r2[i] * (global_best[i] - current_position[i]) for i in range(len(current_velocity))]
        
        max_velocity = max(1, int(len(current_velocity) * self.velocity_factor))
        new_velocity = [round(inertia[i] + cognitive[i] + social[i]) for i in range(len(current_velocity))]
        new_velocity = [max(min(v, max_velocity), -max_velocity) for v in new_velocity]  # Apply velocity limits

        return new_velocity

    def applyVelocity(self,p_position, p_velocity):
        new_position = []
        client_count = len(p_position)

        for a, b in zip(p_position, p_velocity):
            np = (a + b) % client_count  

            while np in new_position:
                np = (np + 1) % client_count  

            new_position.append(np)

        return new_position

    def get_next_particle(self):
        self.particle_counter += 1
        if(self.particle_counter >= len(self.swarm.particles)):
            self.iter_counter += 1
            self.particle_counter = 0
        return self.swarm.particles[self.particle_counter].pos

    def optimize(self,total_processing_delay):    

        if(self.swarm.particles[self.particle_counter].best_pos_fitness == None):   
            self.swarm.particles[self.particle_counter].fitness = self.processing_fitness(total_processing_delay)
            self.swarm.particles[self.particle_counter].best_pos_fitness = self.swarm.particles[self.particle_counter].fitness
            return

        new_velocity = self.updateVelocity(self.swarm.particles[self.particle_counter].velocity,
                                            self.swarm.particles[self.particle_counter].pos, 
                                            self.swarm.particles[self.particle_counter].best_pos, 
                                            self.swarm.global_best_particle.best_pos, self.iw, self.c1, self.c2)
        new_position = self.applyVelocity(self.swarm.particles[self.particle_counter].pos, new_velocity)

        new_pos_fitness = self.processing_fitness(total_processing_delay)

        self.swarm.particles[self.particle_counter].pos = new_position
        self.swarm.particles[self.particle_counter].fitness = new_pos_fitness
        self.swarm.particles[self.particle_counter].velocity = new_velocity
        
        if self.swarm.particles[self.particle_counter].fitness > self.swarm.particles[self.particle_counter].best_pos_fitness :  
            self.swarm.particles[self.particle_counter].best_pos = self.swarm.particles[self.particle_counter].pos.copy()
            self.swarm.particles[self.particle_counter].best_pos_fitness = copy.copy(self.swarm.particles[self.particle_counter].fitness)

            if self.swarm.particles[self.particle_counter].fitness > self.swarm.global_best_particle.fitness:
                self.swarm.global_best_particle = copy.deepcopy(self.swarm.particles[self.particle_counter])              
        
        self.tpd_buffer.append(total_processing_delay)

        self.particles_fitnesses_buffer.append(self.swarm.particles[self.particle_counter].fitness)

        
        #root = reArrangeHierarchy(new_position)
        
        

            # iw = 0.15 - ((0.14 * counter) / max_iter) 

            # iterations.append(counter)
            
            # gbest_particle_fitness_results.append(swarm.global_best_particle.fitness)
            # tpd_tuples.append(tpd_buffer.copy())
            # particles_fitnesses_tuples.append(particles_fitnesses_buffer.copy()) # We could simply reverse the TPD plot and get Particles Fitnesses Plot but as the fitness function might change later this method is not reliable 
            
            # particles_row = [counter] + [round(fitness , 2) for fitness in particles_fitnesses_buffer]
            # csv_rows[0].append(particles_row)
            
            # swarm_best_row = [counter, round(swarm.global_best_particle.fitness , 2)]
            # csv_rows[1].append(swarm_best_row)
            
            # tpd_row = [counter] + [round(tpd , 2) for tpd in tpd_buffer]
            # csv_rows[2].append(tpd_row)


            # system("clear")
        
            # print("Iteration : " , counter)
            
            # tpd_buffer.clear()
            # particles_fitnesses_buffer.clear()
            


        # save_data_to_csv(csv_cols[0] , csv_rows[0] , csv_particles_data_path)
        # save_data_to_csv(csv_cols[1] , csv_rows[1] , csv_swarm_best_data_path)
        # save_data_to_csv(csv_cols[2] , csv_rows[2] , csv_tpd_data_path)
        # save_metadata_to_json(json_pso_dict , json_path)

        # illustrate_plot(gbest_particle_fitness_results , sbpfl , sbpft , swarm_best_fitness_fig_path)
        # plot_tuple_curves(particles_fitnesses_tuples , pfl , pft , particles_fitness_fig_path)
        # plot_tuple_curves(tpd_tuples , tpdl , tpdt , tpd_fig_path)
        