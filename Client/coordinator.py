from Core.sdflmq_coordinator_logic import DFLMQ_Coordinator
import time

userID = input("Enter UserID: ")
print("User with ID=" + userID +" is created.")

exec_program = DFLMQ_Coordinator(   myID = userID,
                                    broker_ip = 'localhost' ,
                                    broker_port = 1883,
                                    # introduction_topic='client_introduction',
                                    # controller_executable_topic='controller_executable',
                                    # controller_echo_topic="echo",
                                    start_loop=False,
                                    plot_stats=True
)


exec_program.parallel_loop()
for i in range(10):
    print("runnning separately to show parallel run is working ...")
    time.sleep(1)

exec_program.end_parallel_loop()