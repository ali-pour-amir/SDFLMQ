from Global.executable_class import PubSub_Base_Executable
import json
import ast
class DFLMQ_Coordinator(PubSub_Base_Executable) :

    def __init__(self , 
                myID : str , 
                broker_ip : str , 
                broker_port : int , 
                introduction_topic : str , 
                controller_executable_topic : str , 
                controller_echo_topic : str ,
                start_loop : bool) -> None : 
        
        self.CoTClT = "Coo_to_Cli_T" # publish 
        self.CiTCoT = "Cli_to_Coo_T" # subscribe

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
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)
        
        self.client.subscribe(self.CiTCoT)

        self.sessions = []
        self.active_session = {}
        self.client_stats = {}


    #         'cpu_count'     : psutil.cpu_count() ,
    #         'disk_usage'    : psutil.disk_usage("/") ,
    #         'cpu_frequency' : psutil.cpu_freq() ,
    #         'cpu_stats'     : psutil.cpu_stats() ,
    #         'net_stats'     : psutil.net_if_stats() ,
    #         'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
    #         'net_counters'  : psutil.net_io_counters()}


    clients_sent_local_params = {}

    client_parse_count = 0

    def parse_client_stats(self , client_id, statsstr) : 
        stats = json.loads(statsstr)
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
            
            

        self.client_parse_count += 1


        print(self.client_parse_count)
        if(self.client_parse_count == int(self.active_session["num_clients"])):
            print("all clients participated. Setting up aggregator and initiating training.")
            self.client_parse_count = 0
            self.assign_aggregator()
            self.initiate_training()
    


    def assign_aggregator(self):   
        client0 = next(iter(self.client_stats))
        min_ram_usage = self.client_stats[client0]['ram_usage'][self.active_session['current_round']]
        for client in self.client_stats:
            if(self.client_stats[client]['ram_usage'][self.active_session['current_round']] < min_ram_usage):
                min_ram_usage = self.client_stats[client]['ram_usage'][self.active_session['current_round']]
                client0 = client
        print("Elected client " + client0 + " due to minimum ram usage of " + str(min_ram_usage))
        self.active_session['rounds'][self.active_session['current_round']]['aggregator'] = client0
        self.publish(self.CoTClT,"set_aggregator"," -id " + client0)

    def initiate_training(self):
        self.publish(self.CoTClT,"client_update"," -num_epochs " + str(self.active_session['num_epochs']) + " -batch_size " + str(self.active_session['batch_size']) )
    
    def order_client_resources(self) : 
        self.publish(self.CoTClT , "echo_resources" , "")

    #run new_training_session -session_name se1 -dataset_name MNIST -model_name MNISTMLP -num_clients 2 -num_rounds 100
    #run new_training_session -session_name CIFAR10_VGG3_se1 -dataset_name CIFAR10 -model_name VGG3 -num_clients 2 -num_epochs 1 -batch_size 100 -num_rounds 10
    def create_new_session(self,session,dataset,model,num_clients, num_epochs, batch_size, rounds):
        new_session = {}
        new_session['session_name'] = session
        new_session['dataset_name'] = dataset
        new_session['model_name'] = model
        new_session['num_clients'] = int(num_clients)
        new_session['num_epochs'] = int(num_epochs)
        new_session['batch_size'] = int(batch_size)
        new_session['num_rounds'] = int(rounds)
        new_session['current_round'] = 0
        round = {'participants' : [], 'status': '', 'aggregator':'','acc':'','loss':''}
        new_session['rounds'] = [round]
        self.active_session = new_session
        self.sessions.append(new_session)
        self.sessions.append(new_session)
        print("New training session created. Waiting for FL Initiation command.")
    
    def Initiate_FL(self):
        self.order_client_resources()

    def Pause_FL(self):
        return
    def Stop_FL(self):
        return
    def Resume_FL(self):
        return
    
    def Prepare_Aggregation(self):
        print("Asking aggregator to perform aggregation")
        self.publish(self.CoTClT,"fed_average","")
         
    def update_rounds(self):
        
        self.active_session['rounds'][self.active_session['current_round']]['status'] = 'complete'
        
        if(self.active_session['current_round'] < self.active_session['num_rounds']-1):
            self.active_session['current_round'] += 1
            new_round = {'participants' : [], 'status': '', 'aggregator':''}
            self.active_session['rounds'].append(new_round)
            self.order_client_resources()
        else:
            print("Max number of trainings reached. Session is complete. Saving logs")
            self.save_logs()

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
            if(len(self.active_session['rounds'][self.active_session['current_round']]['participants']) == self.active_session['num_clients']-1):
                print("Max number of participating clients reached. \nNumber of clients: " + str(self.active_session['num_clients']))
                for c in self.active_session['rounds'][self.active_session['current_round']]['participants']:
                    self.publish(self.CoTClT,"send_local", " -id " + c)
                print("Asked clients to send their local model to the aggregator.")
        
        

    def execute_on_msg(self, header_parts, body) -> None :
        super().execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'initiate_fl' : 
            self.Initiate_FL()

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources()

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
            client_id = body.split(' -id ')[1].split(' -model_acc ')[0]
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
            model_loss = body.split(' -model_loss ')[1].split(';')[0]
            self.active_session['rounds'][self.active_session['current_round']]['acc'] = str(model_acc)
            self.active_session['rounds'][self.active_session['current_round']]['loss'] = str(model_loss)
            print("Client " + client_id + " has reported aggregation is complete. Requesting for global model propagation.")
            self.publish(self.CoTClT,"propagate_global","")
        
        if(header_parts[2] == 'global_model_propagated'):
            print("Global model propagated. Completing round.")
            self.update_rounds()








userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Coordinator(   myID = userID,
                                    broker_ip = 'localhost' ,
                                    broker_port = 1883,
                                    introduction_topic='client_introduction',
                                    controller_executable_topic='controller_executable',
                                    controller_echo_topic="echo",
                                    start_loop=False
)

exec_program.base_loop()


