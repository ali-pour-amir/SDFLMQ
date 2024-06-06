from Global.executable_class import PubSub_Base_Executable
import json

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

    client_parse_count = 0
    def parse_client_stats(self , client_id, stats) : 
        if(client_id in self.client_stats):
            self.client_stats[client_id]['cpu_count'].append(stats['cpu_count'])
            self.client_stats[client_id]['disk_usage'].append(stats['disk_usage'])
            self.client_stats[client_id]['cpu_frequency'].append(stats['cpu_frequency'])
            self.client_stats[client_id]['cpu_stats'].append(stats['cpu_stats'])
            self.client_stats[client_id]['net_stats'].append(stats['net_stats'])
            self.client_stats[client_id]['ram_usage'].append(stats['ram_usage'])
            self.client_stats[client_id]['net_counters'].append(stats['net_counters'])
        else:
            self.client_stats[client_id]['cpu_count']      =  [stats['cpu_count']]
            self.client_stats[client_id]['disk_usage']     =  [stats['disk_usage']]
            self.client_stats[client_id]['cpu_frequency']  =  [stats['cpu_frequency']]
            self.client_stats[client_id]['cpu_stats']      =  [stats['cpu_stats']]
            self.client_stats[client_id]['net_stats']      =  [stats['net_stats']]
            self.client_stats[client_id]['ram_usage']      =  [stats['ram_usage']]
            self.client_stats[client_id]['net_counters']   =  [stats['net_counters']]
            
        
        self.client_parse_count += 1
        if(self.client_parse_count == self.active_session["num_clients"]):
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
        self.publish(self.CoTClT,"client_update","")
    
    def order_client_resources(self) : 
        self.publish(self.CoTClT , "echo_resources" , "")

    def create_new_session(self,session,dataset,model,num_clients, rounds):
        new_session = {}
        new_session['session_name'] = session
        new_session['dataset_name'] = dataset
        new_session['model_name'] = model
        new_session['num_clients'] = num_clients
        new_session['num_rounds'] = rounds
        new_session['current_round'] = 0
        round = {'participants' : [], 'status': '', 'aggregator':''}
        new_session['rounds'] = [round]
        self.active_session = new_session
        self.sessions.append(new_session)
        self.sessions.append(new_session)
        self.Initiate_FL()
    
    
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
        new_round = {'participants' : [], 'status': '', 'aggregator':''}
        self.active_session['rounds'].append(new_round)
        self.active_session['rounds'][self.active_session['current_round']]['status'] = 'complete'
        if(self.active_session['current_round'] < self.active_session['num_rounds']):
            self.active_session['current_round'] += 1
            self.order_client_resources()
        else:
            print("Max number of trainings reached. Session is complete. Saving logs")
    
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
            if(len(self.active_session['rounds'][self.active_session['current_round']]['participants']) == self.active_session['num_clients']):
                print("Max number of participating clients reached. \nNumber of clients: " + self.active_session['num_clients'] + "\nInitiating preparation for Aggregation.")
                self.Prepare_Aggregation()

    def execute_on_msg(self, header_parts, body) -> None :
        super().execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources()

        if header_parts[2] == 'parse_client_stats' : 
            self.parse_client_stats( header_parts[0],body)

        if(header_parts[2] == 'new_training_session'):
            session_name    = body.split(' -session_name ')[1]  .split(' -dataset_name ')[0]
            dataset_name    = body.split(' -dataset_name ')[1]  .split(' -model_name ')[0]
            model_name      = body.split(' -model_name ')[1]    .split(' -num_clients ')[0]
            num_clients     = body.split(' -num_clients ')[1]   .split(' -num_rounds ')[0]
            num_rounds      = body.split(' -num_rounds ')[1]    .split(';')[0]
            self.create_new_session(session_name,
                                    dataset_name,
                                    model_name,
                                    num_clients,
                                    num_rounds)

        if(header_parts[2] == 'local_training_complete'):
            client_id = body.split(' -id ')[1].split(';')[0]
            print("checking client " + client_id + " as its training for the round is finished.")
            self.check_participant(client_id)

        if(header_parts[2] == 'aggregation_complete'):
            client_id = body.split(' -id ')[1].split(';')[0]
            print("Client " + client_id + " has reported aggregation is complete. Completing round.")
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


