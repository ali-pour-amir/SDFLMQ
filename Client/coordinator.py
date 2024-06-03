from Global.executable_class import PubSub_Base_Executable

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
        
    def Initiate_FL(self, dataset_name, model_name, num_rounds):
        
        return
    def parse_client_stats(self , msg) : 
        print(msg)

    def execute_on_msg(self, header_parts, body) -> None :
        super().execute_on_msg(header_parts, body) 
        # header_parts = self._get_header_body(msg)

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources()

        if header_parts[2] == 'parse_client_stats' : 
            self.parse_client_stats(body)

    def order_client_resources(self) : 
        self.publish(self.CoTClT , "echo_resources" , "")


userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Coordinator(myID = userID,
        broker_ip = 'localhost' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)

exec_program.base_loop()


