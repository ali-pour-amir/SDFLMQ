import numpy as np
import matplotlib.pyplot as plt

plt.axis([0, 100, 0, 100])

x = []
y = []
z = []
for i in range(100):
    x.append(i)
    rand = np.random.randint(0,100)
    y.append(rand)
    z.append(100 - rand)
    plt.plot(x,y,color='blue')
    plt.plot(x, z,color='red')
    plt.pause(0.5)

plt.show()