from Core.Base.executable_class import PubSub_Base_Executable
from Core.Base.topics import SDFLMQ_Topics
from Core.Modules.Coordinator_Modules.session_manager import Session_Manager
from Core.Modules.Coordinator_Modules.clustering_engine import Clustering_Engine
from Core.Modules.Coordinator_Modules.load_balancer import Load_Balancer

import json
import ast
import matplotlib.pyplot as plt
import threading
import random

class DFLMQ_Coordinator(PubSub_Base_Executable) :

    def __init__(self , 
                myID : str , 
                broker_ip : str , 
                broker_port : int , 
                start_loop : bool,
                plot_stats : bool) -> None : 
        
        topics = SDFLMQ_Topics()
        self.CoTClT = topics.CoTClT # publish 
        self.CiTCoT = topics.ClTCoT # subscribe

        self.session_manager = Session_Manager()
        self.clustering_engine = Clustering_Engine()
        self.load_balancer = Load_Balancer()
        
        self.executables.append('order_client_resources')
        self.executables.append('parse_client_stats')
        self.executables.append('new_training_session')
        self.executables.append('initiate_fl')
        self.executables.append('local_training_complete')
        self.executables.append('aggregation_complete')
        self.executables.append('aggregator_received_local_params')
        self.executables.append('global_model_propagated')

        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    start_loop)
        
        self.client.subscribe(self.CiTCoT)



    def parse_client_stats(self , client_id, statsstr) : 

        stats = json.loads(statsstr)
        round_status = self.active_session['rounds'][self.active_session['current_round']]['status'] 

        if((round_status != 'pending') and (round_status != 'complete')):
            if(client_id in self.client_stats):
                self.client_stats[client_id]['cpu_count'].append(stats['cpu_count'])
                # self.client_stats[client_id]['disk_usage'].append(stats['disk_usage'])
                self.client_stats[client_id]['cpu_frequency'].append(stats['cpu_frequency'])
                # self.client_stats[client_id]['cpu_stats'].append(stats['cpu_stats'])
                # self.client_stats[client_id]['net_stats'].append(stats['net_stats'])
                self.client_stats[client_id]['ram_usage'].append(stats['ram_usage'])
                # self.client_stats[client_id]['net_counters'].append(stats['net_counters'])


            else:
                self.client_stats[client_id] = {}
                self.client_stats[client_id]['cpu_count']      =  [stats['cpu_count']]
                # self.client_stats[client_id]['disk_usage']     =  [stats['disk_usage']]
                self.client_stats[client_id]['cpu_frequency']  =  [stats['cpu_frequency']]
                # self.client_stats[client_id]['cpu_stats']      =  [stats['cpu_stats']]
                # self.client_stats[client_id]['net_stats']      =  [stats['net_stats']]
                self.client_stats[client_id]['ram_usage']      =  [stats['ram_usage']]
                # self.client_stats[client_id]['net_counters']   =  [stats['net_counters']]
                
            if((client_id in self.mem_usage_track) == False):
                self.mem_usage_track[client_id] = []
                self.total_mem_usage[client_id] = []

            if(client_id in self.round_clients):
                print("already signed for the round.")
            else:
                self.round_clients.append(client_id)
                self.client_parse_count += 1
                print("newly participated clients for the round: " + str(self.client_parse_count))
            

            if(self.client_parse_count == int(self.active_session["num_clients"])):
                print("all clients participated. Setting up aggregator and initiating training.")
                self.broadcast_trainers()
                self.assign_aggregator(assignment_criteria="random")
                self.initiate_training()
                self.active_session['rounds'][self.active_session['current_round']]['status'] = 'pending'
                
    def broadcast_trainers(self):
        trainers_list = json.dumps(self.round_clients)
        print("Elected clients for training: " + trainers_list)
        self.publish(self.CoTClT, "update_status"," -ids " + trainers_list)
        self.round_clients = []
        self.client_parse_count = 0

    def assign_aggregator(self,assignment_criteria):   
        client0 = next(iter(self.client_stats))

        if(assignment_criteria == "max_mem"):
            min_ram_usage = self.client_stats[client0]['ram_usage'][len(self.client_stats[client0]['ram_usage'])-1]
            for client in self.client_stats:
                client_ram_usage = self.client_stats[client]['ram_usage'][len(self.client_stats[client]['ram_usage'])-1]
                if(client_ram_usage < min_ram_usage):
                    min_ram_usage = client_ram_usage
                    client0 = client
            print("Elected client " + client0 + " due to minimum ram usage of " + str(min_ram_usage))
        elif(assignment_criteria == "random"):
            randc = random.randint(0,len(self.client_stats)-1)
            print(len(self.client_stats))
            print(randc)
            
            client0 = list(self.client_stats.keys())[randc]

            print("Randomly elected client " + client0 + ".")

        self.active_session['rounds'][self.active_session['current_round']]['aggregator'] = client0
        self.publish(self.CoTClT,"set_aggregator"," -id " + client0)

    def initiate_training(self):
        self.publish(self.CoTClT,"client_update"," -num_epochs " + str(self.active_session['num_epochs']) + " -batch_size " + str(self.active_session['batch_size']) )
    
    def order_client_resources(self,model_name, dataset_name) : 
        self.publish(self.CoTClT , "echo_resources" , " -model_name " + model_name + " -dataset_name " + dataset_name)
    
    def plot_accloss(self,acc,loss, rounds = 0, init = False):
      
        if(init == True): 
            self.plot_fig, (self.plot_ax_accloss, self.plot_ax_mem,self.plot_ax_total_mem) = plt.subplots(3,1,layout='constrained') # fig : figure object, ax : Axes object
            self.plot_ax_accloss.set_xlabel('round')
            self.plot_ax_accloss.set_xlim((0,rounds))
            
            self.plot_ax_accloss.set_ylim((0.0,1.0))
            self.plot_ax_accloss.set_ylabel('prediction accuracy')

            self.plot_ax_mem.set_xlim((0,rounds))
            self.plot_ax_mem.set_ylabel('ram usage (bytes)')
            self.plot_ax_mem.set_xlabel('round')

            self.plot_ax_total_mem.set_xlim((0,rounds))
            self.plot_ax_total_mem.set_ylabel('total ram usage (bytes)')
            self.plot_ax_total_mem.set_xlabel('round')
            
            self.plt_step = []
            self.plt_acc = []
            self.plt_loss = []
        else:
            self.plt_step.append(len(self.plt_step))
            self.plt_acc.append(float(acc))
            self.plt_loss.append(float(loss))
           
        # plt.plot(self.plt_step,self.plt_loss,color='red')

        self.plot_ax_accloss.plot(self.plt_step,self.plt_loss,color='red')
        self.plot_ax_accloss.plot(self.plt_step,self.plt_acc,color='blue')
        
        for cl in self.mem_usage_track:
            self.plot_ax_mem.plot(self.plt_step,self.mem_usage_track[cl])

        for cl in self.total_mem_usage:
            self.plot_ax_total_mem.plot(self.plt_step,self.total_mem_usage[cl])
       
        plt.pause(0.1)
        
        # plt.show()

    def create_new_session(self,session,dataset,model,num_clients, num_epochs, batch_size, rounds):
        new_session = {}
        new_session['session_name'] = session
        new_session['dataset_name'] = dataset
        new_session['model_name'] = model
        new_session['num_clients'] = int(num_clients)
        new_session['num_rounds'] = int(rounds)
        new_session['current_round'] = 0
        round = {'participants' : [],
                 'status': '', 
                 'cluster_topology':'',
                 'acc':'',
                 'loss':''}
        
        new_session['rounds'] = [round]

        self.sessions.append(new_session)
        

    def Initiate_FL(self):
        self.order_client_resources(self.active_session['model_name'],self.active_session['dataset_name'])

    def Prepare_Aggregation(self):
        print("Asking aggregator to perform aggregation")
        self.publish(self.CoTClT,"fed_average","")
         
    def update_rounds(self):
        
        self.active_session['rounds'][self.active_session['current_round']]['status'] = 'complete'
        
        if(self.active_session['current_round'] < self.active_session['num_rounds']-1):
            self.active_session['current_round'] += 1
            new_round = {'participants' : [], 'status': '', 'aggregator':''}
            self.active_session['rounds'].append(new_round)
            self.order_client_resources(self.active_session['model_name'],self.active_session['dataset_name'])
        else:
            print("Max number of trainings reached. Session is complete. Saving logs")
            self.save_logs()
            if(self.plot_stats):
                plt.show()

    def save_logs(self):
        session_file = open(self.root_directory + "/"+self.active_session['session_name']+".txt",'w')
        client_stats_file = open(self.root_directory + "/"+self.active_session['session_name']+"_client_stats.txt",'w')
        json.dump(self.active_session,session_file)
        json.dump(self.client_stats,client_stats_file)

    def check_participant(self,client_id):
        if(client_id in self.active_session['rounds'][self.active_session['current_round']]['participants']):
            print("client " + client_id + " has already acknowledged training is complete.")
        else:
            self.active_session['rounds'][self.active_session['current_round']]['participants'].append(client_id)
            max_participants_th = self.active_session['num_clients']
            print("Aggregator is " + self.active_session['rounds'][self.active_session['current_round']]['aggregator'])
            print("Participants are " + str(self.active_session['rounds'][self.active_session['current_round']]['participants']))
            # if( self.active_session['rounds'][self.active_session['current_round']]['aggregator'] in  self.active_session['rounds'][self.active_session['current_round']]['participants']):
            #     max_participants_th -= 1
            if(len(self.active_session['rounds'][self.active_session['current_round']]['participants']) == max_participants_th):
                print("Max number of participating clients reached. \nNumber of clients: " + str(self.active_session['num_clients']))
                for c in self.active_session['rounds'][self.active_session['current_round']]['participants']:
                    self.publish(self.CoTClT,"send_local", " -id " + c)
                print("Asked clients to send their local model to the aggregator.")
        



    def request_client_stats(self,session_id):
        self.publish(topic=session_id,func_name="report_client_stats",msg="")

    def __execute_on_msg(self, header_parts, body) -> None :
        super().__execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'initiate_fl' : 
            self.Initiate_FL()

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources(self.active_session['model_name'],self.active_session['dataset_name'])

        if header_parts[2] == 'parse_client_stats' : 
            self.parse_client_stats( header_parts[0],body)

        if header_parts[2] == 'new_training_session':
            
            session_name    = body.split(' -session_name ')[1]  .split(' -dataset_name ')[0]
            dataset_name    = body.split(' -dataset_name ')[1]  .split(' -model_name ')[0]
            model_name      = body.split(' -model_name ')[1]    .split(' -num_clients ')[0]
            num_clients     = body.split(' -num_clients ')[1]   .split(' -num_epochs ')[0]
            num_epochs     = body.split(' -num_epochs ')[1]   .split(' -batch_size ')[0]
            batch_size     = body.split(' -batch_size ')[1]   .split(' -num_rounds ')[0]
            num_rounds      = body.split(' -num_rounds ')[1]    .split(';')[0]
            self.create_new_session(session_name,
                                    dataset_name,
                                    model_name,
                                    num_clients,
                                    num_epochs,
                                    batch_size,
                                    num_rounds)

        if(header_parts[2] == 'local_training_complete'):
            client_id = body.split(' -id ')[1].split(' -mem ')[0]
            mem_usage = int(body.split(' -mem ')[1].split(';')[0])

            self.mem_usage_track[client_id].append(mem_usage)
            if(len(self.total_mem_usage[client_id]) > 0):
                self.total_mem_usage[client_id].append(mem_usage + self.total_mem_usage[client_id][len(self.total_mem_usage[client_id])-1])
            else:
                self.total_mem_usage[client_id].append(mem_usage)
            
            
            # model_acc = body.split(' -model_acc ')[1].split(' -model_loss ')[0]
            # model_loss = body.split(' -model_loss ')[1].split(';')[0]
            print("checking client " + client_id + " as its training for the round is finished.")
            self.check_participant(client_id,
                                #    model_acc,
                                #    model_loss
                                   )

        if(header_parts[2] == 'aggregator_received_local_params'):
            client_id = body.split(' -id ')[1].split(';')[0]
            if(client_id in self.active_session['rounds'][self.active_session['current_round']]['participants']):
                print("Aggregator received model params of client " + client_id)
                self.clients_sent_local_params[client_id] = 1
                if(len(self.clients_sent_local_params) == len(self.active_session['rounds'][self.active_session['current_round']]['participants'])):
                    print("All clients sent their locals. Initiating aggregation.")
                    self.clients_sent_local_params = {}
                    self.Prepare_Aggregation()
            else:
                print("not in the list")
        
        if(header_parts[2] == 'aggregation_complete'):
            client_id = body.split(' -id ')[1].split(' -model_acc ')[0]
            model_acc = body.split(' -model_acc ')[1].split(' -model_loss ')[0]
            model_loss = body.split(' -model_loss ')[1].split(' -mem ')[0]
            
            mem_usage = int(body.split(' -mem ')[1].split(';')[0])
            self.mem_usage_track[client_id][len(self.mem_usage_track[client_id])-1] += mem_usage 
            self.total_mem_usage[client_id][len(self.total_mem_usage[client_id])-1] += mem_usage 
           

            self.active_session['rounds'][self.active_session['current_round']]['acc'] = str(model_acc)
            self.active_session['rounds'][self.active_session['current_round']]['loss'] = str(model_loss)
            print("Client " + client_id + " has reported aggregation is complete. Requesting for global model propagation.")

            if(self.plot_stats == True):
                self.plot_accloss(model_acc,model_loss,0,False)
                
            self.publish(self.CoTClT,"propagate_global","")
        
        if(header_parts[2] == 'global_model_propagated'):
            print("Global model propagated. Completing round.")
            self.update_rounds()

    def __new_fl_session_request(self,client_id,
                                    session_id,
                                    session_time,
                                    session_capacity_min,
                                    session_capacity_max, 
                                    waiting_time, 
                                    model_name):
        self.create_new_session()
    

    
