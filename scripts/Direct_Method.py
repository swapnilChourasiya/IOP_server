import numpy as np
import pandas as pd
import sys
import math
import json


line_data = json.loads(sys.argv[1])
df = pd.DataFrame(line_data)
# print(df)

n = df.shape[0]
bibc = np.zeros([n, n])
bcbv = np.zeros([n, n], dtype = complex)
load = np.zeros([n, 1], dtype = complex)


#BIBC matrix calculation
for i in range(n):
    #branch from bus a to bus b
    a = df.iat[i, 1] #sending bus
    b = df.iat[i, 2] #receiving bus
    if a != 1:
        for j in range(n):
            bibc[j][b-2] = bibc[j][a-2]
    bibc[i][b-2] = 1 #no of phases between bus a and b

#BCBV matrix calculation
for i in range(n):
    #branch from bus a to bus b
    a = df.iat[i, 1] #sending bus
    b = df.iat[i, 2] #receiving bus
    z = df.iat[i, 3] + 1j*df.iat[i, 4] #impedance R + jB
    if a != 1:
        for j in range(n):
            bcbv[b-2][j] = bcbv[a-2][j]
    bcbv[b-2][i] = z 
    
#load vector calcutions
for i in range(n):
    load[i][0] = df.iat[i, 5] + 1j * df.iat[i, 6] #P + jQ
    
load = load*1000 #since load is given in kV

dlf = bcbv @ bibc #dlf matrix 

Vs = 11000 + 0j #base voltage and initial guess of all buses
BV = np.full(shape = (n, 1), fill_value = Vs) # Initial Guess of bus voltage matrix

#Running iterations till convergence
error = 1
num = 0
while error > 0.1:
    BC = np.conjugate(np.divide(load, BV)) 
    BV_new = Vs - dlf@BC
    error = (np.amax(abs(abs(BV_new)-abs(BV))))
    BV = BV_new
    num = num + 1
    

# print("Number of iterations is :", num)
# print("\nVoltage magnitude:-")
mag = abs(BV)/1000
for i in range(n):
    mag[i][0] = round(mag[i][0], 3)
# print(mag)
# print("\nVoltage angle:-")
ang = np.angle(BV)*180/math.pi
for i in range(n):
    ang[i][0] = round(ang[i][0], 3)
# print(ang)

arr = []
for i in range(n):
    arr.append("V" + str(i+2))

output = pd.DataFrame(arr, columns=['Branch Number'])
output.set_index('Branch Number', inplace = True)
output['Voltage_magnitude'] = mag
output['Voltage_angle'] = ang
# print(output)print
result = output.to_json(orient = 'records')
print(result)


sys.stdout.flush()
