#CS 4501: CCC HW2 by Mvy3ns

import sys, random

#STEP 1: Finite Fields Arithmetic Functions
def finiteAddition(x, y, p):
    return (x+y) % p

def finiteMultiplication(x, y, p):
    return (x*y) % p

def finiteSubtraction(x, y, p):
    sum = x + findAdditiveInverse(y, p)
    if sum < 0:
        while sum < 0:
            sum += p
    else:
        sum %= p
    return sum

def finiteDivision(x, y, p):
    y = findMultiplicativeInverse(y, p)
    return (x * y) % p

def finiteExponentiation(x, y, p):
    return (x**y) % p

def findAdditiveInverse(x, p):
    return p + x

def findMultiplicativeInverse(x, p):
    return x**(p-2) % p

#Part 2: EC Operations
def ecSelfAddition(x, y, p):
    m = (3*(x**2)) * findMultiplicativeInverse((2*y), p) 
    m = m % p

    x3 = (m**2 - (2*x))
    while (x3 < 0):
        x3 += p
    x3 = x3 % p

    y3 = (m*(x-x3) - y)
    while (y3 < 0):
        y3 += p
    y3 = y3 % p
    return (x3, y3)

def ecAddition(x1, y1, x2, y2, p):
    m = (y2 - y1) * findMultiplicativeInverse(x2 - x1, p)
    m = m % p

    x3 = (m**2 - x1 - x2)
    while (x3 < 0):
        x3 += p
    x3 = x3 % p

    y3 = (m*(x1 - x3) - y1)
    while (y3 < 0):
        y3 += p
    y3 = y3 % p

    return (x3, y3)

def ecScalarMultiplication(k, Q, p):
    binary = str(bin(k))
    memory = [(Q[0], Q[1])]

    sum = (0, 0)

    for i in range(1, len(binary)-2):
        (x, y) = ecSelfAddition(memory[i-1][0], memory[i-1][1], p)
        memory.append((x, y))

    index = 0
    for i in range(len(binary)-1, 1, -1):
        if binary[i] == "1":
            if sum == (0,0):
                sum = (memory[index][0], memory[index][1])
            else:
                sum = ecAddition(sum[0], sum[1], memory[index][0], memory[index][1], p)
        index+=1
    return sum

#PART 3: Signatures

#Global Curve constant
a = 0
b = 7

def generateKeys(p, o, G):
    d = random.randrange(1, int(o)-1)
    Q = ecScalarMultiplication(d, G, p)

    return d, Q

def signMessage(p, o, G, d, h):
    r = 0
    s = 0

    while (r == 0 | s == 0):
        k = random.randrange(1, o-1)
        k_inverse = findMultiplicativeInverse(k, o)

        r = ecScalarMultiplication(k, G, p)[0]
        s = (k_inverse * (h + r * d)) % o

    return (r, s)

def verifyMessage(p, o, G, Q, signature, h):
    r = signature[0]
    s = signature[1]

    s_inverse = findMultiplicativeInverse(s, o)

    scalar1 = (s_inverse * h) % o
    left = ecScalarMultiplication(scalar1, G, p)

    scalar2 = (s_inverse * r) % o
    right = ecScalarMultiplication(scalar2, Q, p)

    R = ecAddition(left[0], left[1], right[0], right[1], p)  

    return r == R[0]


#Part 4: Commands (like main)

mode = sys.argv[1]

if mode == "userid":
    print("mvy3ns")
else:
    p = int(sys.argv[2])
    o = int(sys.argv[3])
    Gx = int(sys.argv[4])
    Gy = int(sys.argv[5])

if mode == "genkey":
    d, Q = generateKeys(p, o, (Gx, Gy))
    print(d)
    print(Q[0])
    print(Q[1])

if mode == "sign":
    d = int(sys.argv[6])
    h = int(sys.argv[7])

    signature = signMessage(p, o, (Gx, Gy), d, h)

    print(signature[0])
    print(signature[1])

if mode == "verify":
    Qx = int(sys.argv[6])
    Qy = int(sys.argv[7])
    r = int(sys.argv[8])
    s = int(sys.argv[9])
    h = int(sys.argv[10])

    valid = verifyMessage(p, o, (Gx, Gy), (Qx, Qy), (r, s), h)

    print(str(valid))