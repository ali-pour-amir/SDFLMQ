from Base.executable_class import PubSub_Base_Executable

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

        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        
    def _get_header_body(self , msg) -> list :
        header_body = str(msg.payload.decode()).split('::')
        print("MESSAGE Header: " + header_body[0])

        header_parts = header_body[0].split('|')
        return header_parts

    def execute_on_msg(self, client, userdata, msg) -> None :
        super().execute_on_msg(client, userdata, msg) 
        header_parts = self._get_header_body(msg)

        if header_parts[2] == 'order_client_resources' : 
            self.order_client_resources()

    def order_client_resources(self) : 
        self.publish(self.CoTClT , "echo_resources" , "")


userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Coordinator(myID = userID,
        broker_ip = 'broker.emqx.io' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)

exec_program.base_loop();
