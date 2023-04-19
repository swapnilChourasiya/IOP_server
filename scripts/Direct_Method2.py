import numpy as np
import pandas as pd
import re
import json
import math
import sys



a = sys.argv[1]
line_data = json.loads(a)
linedata = pd.DataFrame(line_data) # line data --> Node A || Node B || Length || config

a = sys.argv[2]
load_data = json.loads(a) # load_data --> identity || type || ph1 || ph1 || ...
loaddata = pd.DataFrame(load_data)

a = sys.argv[3]
config_data = json.loads(a) # config data --> identity || 9 R and X values
configdata = pd.DataFrame(config_data)

a = sys.argv[4]
trans_data = json.loads(a) # trans data --> name || Power || high kv || low kv || R || X
transdata = pd.DataFrame(trans_data)

a = sys.argv[5]
dist_data = json.loads(a) # dist data--> Node A || node B || type || ph1 || ph 1 ....
distdata = pd.DataFrame(dist_data)

a = sys.argv[6]
shunt_data = json.loads(a) # shunt data --> Node || ph-1 || ph-2 || ph-3
shuntdata = pd.DataFrame(shunt_data)

sb = transdata.iat[0, 1] # Base power of the root node in KVA

n = linedata.shape[0] # Number of Branches = Number of Buses - 1 (not including Bus 1)
m = distdata.shape[0] # extra buses to be created for distributed loads

typ = {}
vb = {}
vb[0] = float(re.findall(r"[-+]?(?:\d*\.*\d+)", transdata.iat[0, 3])[0])

# map creation
size = configdata.shape[0]
configMap = {}
for i in range(size):
    configMap[configdata.iat[i, 0]] = i

       
size = transdata.shape[0]        
transMap = {}
for i in range(size):
    transMap[transdata.iat[i, 0]] = i

nodeTree = {}
nodeSet = set()
nodeMap = {}
counter = 0
for i in range(n):
    if linedata.iat[i, 0] not in nodeTree:
        nodeTree[linedata.iat[i, 0]] = []
    if linedata.iat[i, 1] not in nodeTree:
        nodeTree[linedata.iat[i, 1]] = []
    nodeTree[linedata.iat[i, 0]].append(linedata.iat[i, 1])
    nodeSet.add(linedata.iat[i, 0])
    
for i in range(n):
    nodeSet.discard(linedata.iat[i, 1])
    
root = nodeSet.pop()  

def dfs(a):
    global counter
    if a in distdata["Node B"].values: # to create extra nodes for distributed loads
        typ[counter] = 3
        counter += 1
        nodeMap[a] = counter
        typ[counter] = 2
        counter += 1
    else:
        nodeMap[a] = counter
        typ[counter] = 1
        counter += 1
    for b in nodeTree[a]:
        dfs(b)

dfs(root)      

newOrder = []
for i in range(n):
    newOrder.append(nodeMap[linedata.iat[i, 1]] - 1)

linedata['key'] = newOrder
linedata.sort_values(by=['key'], inplace = True)
linedata.reset_index(drop = True, inplace = True)

# phase array construction
phase = np.zeros((n+m+1, 3)) # Phase A | Phase B | Phase C
phase[0, 0] = 1 # Root Node
phase[0, 1] = 1
phase[0, 2] = 1

for i in range(n):
    a = nodeMap[linedata.iat[i, 0]] # Node number of parent node
    b = nodeMap[linedata.iat[i, 1]] # Node Number of child node
    if typ[b] == 2:
        # thus a distributed load line
        k = configMap[linedata.iat[i, 3]] # index of this branch's configuration in configdata
        if configdata.iat[k, 1] != 0 or configdata.iat[k, 2] != 0:
            phase[b,0] = 1
            phase[b-1, 0] = 1
        if configdata.iat[k, 9] != 0 or configdata.iat[k, 10] != 0:
            phase[b,1] = 1
            phase[b-1, 1] = 1
        if configdata.iat[k, 17] != 0 or configdata.iat[k, 18] != 0:
            phase[b,2] = 1
            phase[b-1, 2] = 1
    else:
        # thus not a distributed load line
        if linedata.iat[i, 3] not in transMap:
            if linedata.iat[i, 3] == 'Switch':
                # thus a switch    
                phase[b, 0] = phase[a, 0]
                phase[b, 1] = phase[a, 1]
                phase[b, 2] = phase[a, 2]  
            else:    
                # thus a normal line
                k = configMap[linedata.iat[i, 3]] # index of this branch's configuration in configdata
                if configdata.iat[k, 1] != 0 or configdata.iat[k, 2] != 0:
                    phase[b,0] = 1
                if configdata.iat[k, 9] != 0 or configdata.iat[k, 10] != 0:
                    phase[b,1] = 1
                if configdata.iat[k, 17] != 0 or configdata.iat[k, 18] != 0:
                    phase[b,2] = 1
        else:
            # thus a transformer line
            typ[b] = 4
            phase[b, 0] = phase[a, 0]
            phase[b, 1] = phase[a, 1]
            phase[b, 2] = phase[a, 2]

# BIBC construction
s = 3*(n+m)
bibc = np.zeros((s, s))
for i in range(n):
    a = nodeMap[linedata.iat[i, 0]] # Node number of parent node
    b = nodeMap[linedata.iat[i, 1]] # Node Number of child node
    
    if typ[b] == 2:
        c = b-1
        
        if a != 0:
            # for branches not emanating from the root node
            for x in range(3):
                if phase[c, x] == 1:
                    for j in range(s):
                        bibc[j,3*c-3+x] = bibc[j, 3*a-3+x]
                        
        for x in range(3):
            if phase[c, x] == 1:
                bibc[3*c-3+x, 3*c-3+x] = 1     
        
        for x in range(3):
            if phase[b, x] == 1:
                for j in range(s):
                    bibc[j,3*b-3+x] = bibc[j, 3*c-3+x]
                bibc[3*b-3+x, 3*b-3+x] = 1   
        
    else:
        if a != 0:
            # for branches not emanating from the root node
            for x in range(3):
                if phase[b, x] == 1:
                    for j in range(s):
                        bibc[j,3*b-3+x] = bibc[j, 3*a-3+x]

        for x in range(3):
            if phase[b, x] == 1:
                bibc[3*b-3+x, 3*b-3+x] = 1  

# BCBV construction
s = 3*(n+m)
bcbv = np.zeros((s, s), dtype = complex)
for i in range(n):
    a = nodeMap[linedata.iat[i, 0]] # Node number of parent node
    b = nodeMap[linedata.iat[i, 1]] # Node Number of child node
    
    if typ[b] == 2:
        # Thus distributed load line
        c = b-1 # The new node created
        
        vb[b] = vb[a]
        vb[c] = vb[b]
    
        if a != 0:
            # for branches not emanating from the root node
            for x in range(3):
                if phase[c, x] == 1:
                    for j in range(s):
                        bcbv[3*c-3+x, j] = bcbv[3*a-3+x, j]
                        
        l = linedata.iat[i, 2]/5280 # Length
        
        if phase[b, 0] == 1:
            if phase[b, 1] == 1:
                if phase[b, 2] == 1:
                    index = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                else:
                    index = [1, 2, 4, 5]
            else:
                if phase[b, 2] == 1:
                    index = [1, 3, 7, 9]
                else:
                    index = [1]
        else:
            if phase[b, 1] == 1:
                if phase[b, 2] == 1:
                    index = [5, 6, 8, 9]
                else:
                    index = [5]
            else:
                if phase[b, 2] == 1:
                    index = [9]
                else:
                    index = []

        for t in index:
            bcbv[3*(c-1) + (t-1)//3, 3*(c-1) + (t-1)%3] = (l/2)*(configdata.iat[k, 2*t-1] + 1j*configdata.iat[k, 2*t])*sb/((vb[b]**2)*1000)
        
        for x in range(3):
            if phase[b, x] == 1:
                for j in range(s):
                    bcbv[3*b-3+x, j] = bcbv[3*c-3+x, j]
        
        for t in index:
            bcbv[3*(b-1) + (t-1)//3, 3*(b-1) + (t-1)%3] = (l/2)*(configdata.iat[k, 2*t-1] + 1j*configdata.iat[k, 2*t])*sb/((vb[b]**2)*1000)

                                                             
    elif typ[b] == 4:
        # Thus transformer line
        
        vb[b] = float(re.findall(r"[-+]?(?:\d*\.*\d+)", transdata.iat[transMap[linedata.iat[i, 3]], 3])[0])/vb[0] 
        k = transMap[linedata.iat[i, 3]] # index of the transformer in transdata
        
        if a != 0:
            # for branches not emanating from the root node
            for x in range(3):
                if phase[b, x] == 1:
                    for j in range(s):
                        bcbv[3*b-3+x, j] = bcbv[3*a-3+x, j]
                    
        for x in range(3):
            if phase[b, x] == 1:
                bcbv[3*b-3+x, 3*b-3+x] = (transdata.iat[k, 4] + 1j*transdata.iat[k, 5])*(transdata.iat[k, 1])/(sb * 100)
        
    else:
        # Thus normal line
        
        vb[b] = vb[a] # The voltage base of child node is same as the parent node
        
        if a != 0:
            # for branches not emanating from the root node
            for x in range(3):
                if phase[b, x] == 1:
                    for j in range(s):
                        bcbv[3*b-3+x, j] = bcbv[3*a-3+x, j]
        
        k = configMap[linedata.iat[i, 3]] # index of this branch's configuration in configdata

        if phase[b, 0] == 1:
            if phase[b, 1] == 1:
                if phase[b, 2] == 1:
                    index = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                else:
                    index = [1, 2, 4, 5]
            else:
                if phase[b, 2] == 1:
                    index = [1, 3, 7, 9]
                else:
                    index = [1]
        else:
            if phase[b, 1] == 1:
                if phase[b, 2] == 1:
                    index = [5, 6, 8, 9]
                else:
                    index = [5]
            else:
                if phase[b, 2] == 1:
                    index = [9]
                else:
                    index = []

        l = linedata.iat[i, 2]/5280  # Length
        for t in index:
            bcbv[3*(b-1) + (t-1)//3 , 3*(b-1) + (t-1)%3 ] = l*(configdata.iat[k, 2*t-1] + 1j*configdata.iat[k, 2*t])*sb/((vb[b]**2)*1000)

dlf = bcbv @ bibc

# Load  Matrix Construction
pqLoad = np.empty((0, 4), complex) # node number | ph-1 | ph-2 | ph-3 -- > stores power at each bus phase
zLoad = np.empty((0, 4), complex) # node number | ph-1 | ph-2 | ph-3 -- > stores impedance at each bus phase
iLoad = np.empty((0, 4), complex) # node number | ph-1 | ph-2 | ph-3 -- > stores current injection at each bus phase

size = loaddata.shape[0]
for i in range(size):
    k = nodeMap[loaddata.iat[i, 0]] # index of the bus
    
    l = []
    l.append(k) # bus index at wich this load is connected
    
    if loaddata.iat[i, 1] == "D-PQ" or loaddata.iat[i, 1] == "Y-PQ":
        for x in range(3):
            l.append((loaddata.iat[i, 2*x+2]+1j*loaddata.iat[i, 2*x+3])/sb)
        l = [l]
        pqLoad = np.append(pqLoad, l, axis = 0)
        
    if loaddata.iat[i, 1] == "D-Z" or loaddata.iat[i, 1] == "Y-Z":
        for x in range(3):
            a = (loaddata.iat[i, 2*x+2]+1j*loaddata.iat[i, 2*x+3])
            if a != 0:
                l.append(sb/a)
            else:
                l.append(0) # signifies no connection i.e infinite impedance
        l = [l]
        zLoad = np.append(zLoad, l, axis = 0)
        
    if loaddata.iat[i, 1] == "D-I" or loaddata.iat[i, 1] == "Y-I":
        for x in range(3):
            l.append(np.conjugate((loaddata.iat[i, 2*x+2]+1j*loaddata.iat[i, 2*x+3]))/(sb))
        l = [l]
        iLoad = np.append(iLoad, l, axis = 0)

# Adding distributed loads 

size = distdata.shape[0]
for i in range(size):
    k = nodeMap[distdata.iat[i, 1]] - 1 # index of the new node which was created
    
    l = []
    l.append(k) # bus index at wich this load is connected
    
    if distdata.iat[i, 2] == "D-PQ" or distdata.iat[i, 2] == "Y-PQ":
        for x in range(3):
            l.append((distdata.iat[i, 2*x+3]+1j*distdata.iat[i, 2*x+4])/sb)
        l = [l]
        pqLoad = np.append(pqLoad, l, axis = 0)
        
    if distdata.iat[i, 2] == "D-Z" or distdata.iat[i, 2] == "Y-Z":
        for x in range(3):
            a = (distdata.iat[i, 2*x+3]+1j*distdata.iat[i, 2*x+4])
            if a != 0:
                l.append(sb/a)
            else:
                l.append(0) # signifies no connection i.e infinite impedance
        l = [l]
        zLoad = np.append(zLoad, l, axis = 0)
        
    if distdata.iat[i, 2] == "D-I" or distdata.iat[i, 2] == "Y-I":
        for x in range(3):
            l.append(np.conjugate((distdata.iat[i, 2*x+3]+1j*distdata.iat[i, 2*x+4]))/(sb))
        l = [l]
        iLoad = np.append(iLoad, l, axis = 0)

# Adding shunt capacitors

size = shuntdata.shape[0]
for i in range(size):
    k = nodeMap[shuntdata.iat[i, 0]] # index of the bus at which shunt capacitor is connected
    
    l = []
    l.append(k) # bus index at wich this load is connected
    
    for x in range(3):
        a = ( 1j*-shuntdata.iat[i, x+1])
        if a != 0:
            l.append(sb/a)
        else:
            l.append(0) # signifies no connection i.e infinite impedance
    l = [l]
    zLoad = np.append(zLoad, l, axis = 0)

#iteration

vDrop = np.zeros((s, 1), dtype = complex)
vDropNew = np.zeros((s, 1), dtype = complex)
currIn = np.zeros((s, 1), dtype = complex)
vBase = np.ones((s, 1), dtype = complex)
for i in range(n+m):
    for x in range(3):
        if phase[i+1][x] == 0:
            vBase[3*i+x] = 0
num = 0
error = 1

while error > 0.0001:
    v = vBase - vDrop
    
    currIn = np.zeros((s, 1), dtype = complex)
    # Calculating current injection from voltage estimates
    size = pqLoad.shape[0]
    for i in range(size):
        for x in range(3):
            if v[3*int(pqLoad[i,0])-3+x] != 0:
                currIn[3*int(pqLoad[i,0])-3+x] = np.conjugate((pqLoad[i, x+1])/v[3*int(pqLoad[i,0])-3+x])
    
    size = zLoad.shape[0]
    for i in range(size):
        for x in range(3):
            if zLoad[i, x+1] != 0:
                currIn[3*int(zLoad[i,0])-3+x] += v[3*int(zLoad[i,0])-3+x]/zLoad[i, x+1]
    
    size = iLoad.shape[0]
    for i in range(size):
        for x in range(3):
            currIn[3*int(iLoad[i,0])-3+x] = iLoad[i, x+1]
                 
    #Calculating Voltage drop
    vDropNew = dlf @ currIn
       
    #Error calculation
    error = (np.amax(abs(abs(vBase-vDropNew)-abs(vBase-vDrop))))
    vDrop = vDropNew
    num += 1

# final processing
v = vBase - vDrop
mag = np.array(abs(v))
ang = np.angle(v)*180/math.pi
for i in range(s):
    ang[i][0] = round(ang[i][0], 3)

v_final = np.zeros((n+1, 6))
v_final[0][0] = v_final[0][2] = v_final[0][4] = vb[0]
v_final[0][1] = v_final[0][3] = v_final[0][5] = 0

for i in range(n):
    k = nodeMap[linedata.iat[i, 1]]
    for x in range(3):   
        v_final[i+1][x*2] = mag[3*k-3+x]*vb[k]
        v_final[i+1][x*2] = round(v_final[i+1][x*2], 3)
        v_final[i+1][x*2+1] = ang[3*k-3+x]

results = pd.DataFrame()
results['Bus_Id'] = nodeMap.keys()
results['ph_1_v'] = v_final[:, 0]
results['ph_1_a'] = v_final[:, 1]
results['ph_2_v'] = v_final[:, 2]
results['ph_2_a'] = v_final[:, 3]
results['ph_3_v'] = v_final[:, 4]
results['ph_3_a'] = v_final[:, 5]

results = results.astype('object')
for i in range(n+1):
    for x in range(3):
        if results.iat[i, 2*x+1] == 0:
            results.iat[i, 2*x+1] = '-'
            results.iat[i, 2*x+2] = '-'

# For graph generation

nodes = pd.DataFrame()
edges = pd.DataFrame()

nodes['id'] = nodeMap.keys()
nodes['label'] = nodeMap.keys()
edges['id'] = range(linedata.shape[0])
edges['source'] = linedata['Node A']
edges['target'] = linedata['Node B']
label = []
for i in range(n):
    if typ[nodeMap[linedata.iat[i,1]]] == 4:
        label.append('Xmer')
    else:
        label.append('')
edges['label'] = label   

v_output = results.to_json(orient = 'records')
nodes_output = nodes.to_json(orient = 'records')
edges_output = edges.to_json(orient = 'records')

print(v_output)

sys.stdout.flush()