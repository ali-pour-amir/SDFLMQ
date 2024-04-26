from executable_class import PubSub_Base_Executable
import psutil

class DFLMQ_Client(PubSub_Base_Executable) :
    def __init__(self , 
                 myID : str , 
                 broker_ip : str , 
                 broker_port : int , 
                 introduction_topic : str , 
                 controller_executable_topic : str , 
                 controller_echo_topic : str ,
                 start_loop : bool) -> None : 
        
        self.CoTClT = "Coo_to_Cli_T"
        self.CiTCoT = "Cli_to_Coo_T"
        
        self.executables.append('echo_resources')
        
        super().__init__(
                    myID , 
                    broker_ip , 
                    broker_port , 
                    introduction_topic , 
                    controller_executable_topic , 
                    controller_echo_topic , 
                    start_loop)

        self.client.subscribe(self.CoTClT)
        
    def _get_header_body(self , msg) -> list :
        header_body = str(msg.payload.decode()).split('::')
        print("MESSAGE Header: " + header_body[0])

        header_parts = header_body[0].split('|')
        return header_parts

    def execute_on_msg(self, client, userdata, msg) -> None :
        super().execute_on_msg(client, userdata, msg) 
        header_parts = self._get_header_body(msg)

        if header_parts[2] == 'echo_resources' : 
            self.echo_resources()

    def echo_resources(self) -> None : 
        resources = {
            'cpu_count'     : psutil.cpu_count() ,
            'disk_usage'    : psutil.disk_usage("/") ,
            'cpu_frequency' : psutil.cpu_freq() ,
            'cpu_stats'     : psutil.cpu_stats() ,
            'net_stats'     : psutil.net_if_stats() ,
            'ram_usage'     : psutil.virtual_memory()[3]/1000000000 ,
            'net_counters'  : psutil.net_io_counters() ,
        }

        res_msg = str(resources) # TODO : format the dictionary as string, later 
        self.publish(topic=self.controller_echo_topic,func_name="echo_resources",msg=res_msg)


userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Client(myID = userID,
        broker_ip = 'broker.emqx.io' ,
        broker_port = 1883,
        introduction_topic='client_introduction',
        controller_executable_topic='controller_executable',
        controller_echo_topic="echo",
        start_loop=False
)

exec_program.base_loop();
