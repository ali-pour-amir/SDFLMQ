import Core
from Core.sdflmq_coordinator_logic import DFLMQ_Coordinator
import time

# userID = input("Enter UserID: ")
# print("User with ID=" + userID +" is created.")

coordinator_client = DFLMQ_Coordinator(   myID = 'coord',
                                    broker_ip = 'localhost' ,
                                    broker_port = 1883,
                                    loop_forever=True,
                                    plot_stats=False)


# coordinator_client.parallel_loop()
# for i in range(100):
#     print("runnning separately to show parallel run is working ...")
#     time.sleep(1)
# coordinator_client.end_parallel_loop()