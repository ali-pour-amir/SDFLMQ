
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from Core.sdflmq_client_logic import SDFLMQ_Client
import random
from datetime import datetime, timedelta

# Load the MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize the pixel values to range [0, 1]
x_train, x_test = x_train / 255.0, x_test / 255.0

# One-hot encode the labels
y_train = to_categorical(y_train, num_classes=10)
y_test = to_categorical(y_test, num_classes=10)

# Define the MLP model
model = Sequential([
    Flatten(input_shape=(28, 28)),  # Flatten 28x28 images into a 1D vector
    Dense(128, activation='relu'),  # First hidden layer
    Dense(64, activation='relu'),   # Second hidden layer
    Dense(10, activation='softmax') # Output layer with 10 classes
])

# Compile the model
model.compile(optimizer=Adam(),
              loss='categorical_crossentropy',
              metrics=['accuracy'])


FL_ROUNDS = 11
session_name = "session_02"
# Load MNIST dataset

myid = "client_" + str(random.randint(0,10000))         
fl_client = SDFLMQ_Client(  myID=myid,
                                broker_ip = 'localhost',
                                broker_port = 1883,
                                preferred_role="aggregator",
                                loop_forever=False)
fl_client.create_fl_session(session_id=session_name,
                            session_time=timedelta(hours=1),
                            session_capacity_min= 10,
                            session_capacity_max= 10,
                            waiting_time=timedelta(minutes=10),
                            fl_rounds=FL_ROUNDS,
                            model_name="mlp",
                            preferred_role="aggregator")


for k in range(FL_ROUNDS):
    # Training Loop
    num_epochs = 5
    loss = 0
    model.fit(x_train, y_train, epochs=num_epochs, batch_size=32, validation_data=(x_test, y_test))

    # Evaluate the model on the test set
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
    print(f"Test accuracy: {test_acc:.4f}")
    #Sending the Model for Aggregation
    fl_client.submit_model_stats(session_name,k,test_acc,test_loss)
    fl_client.set_model(session_name,model)
    fl_client.send_local(session_name)
    fl_client.wait_global_update()

    
    




# LOOPING = True
# while(LOOPING):
#     fl_client.oneshot_loop()
#     time.sleep(1)




