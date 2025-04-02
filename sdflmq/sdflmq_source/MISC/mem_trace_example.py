import tracemalloc

# code or function for which memory
# has to be monitored
def app(r):
    
    return r + r
# starting the monitoring
tracemalloc.start()

# function call
x = app([12.2,12])
# print(x)
# displaying the memory
print(tracemalloc.get_traced_memory())

# stopping the library
tracemalloc.stop()

print(x)