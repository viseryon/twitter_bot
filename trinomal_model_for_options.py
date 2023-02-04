import math
import numpy as np
from datetime import datetime as dt
from matplotlib import pyplot as plt
plt.style.use('dark_background')


def crr_trinomial_tree(S, K, r, T, t, v, c_p):

    # S  : spot price
    # K  : strike
    # r  : riskless rate
    # T  : maturity (in yrs.)
    # t  : number of steps
    # v  : annualized volatility
    # c_p  : True of False

    # Calculate time increment
    dt = T / t

    # Set c_p of option
    if c_p:
        x = 1
    else:
        x = -1

    # Initialize tree
    crrTree = np.empty((2 * t + 1, 1))
    crrTree[:] = np.nan

    # Initialize tree parameters
    u = math.exp(v * math.sqrt(2 * dt))
    d = 1/u
    m = 1

    # Pu
    pu = ((math.exp(r*dt/2) - math.exp(-1*v*math.sqrt(dt/2))) /
          (math.exp(v*math.sqrt(dt/2)) - math.exp(-1*v*math.sqrt(dt/2))))**2
    # Pd
    pd = ((math.exp(v*math.sqrt(dt/2)) - math.exp(r*dt/2)) /
          (math.exp(v*math.sqrt(dt/2)) - math.exp(-1*v*math.sqrt(dt/2))))**2
    # Pm
    pm = 1 - (pu + pd)

    for row in range(0, 2*t + 1):

        St = S * u**(max(t - row, 0))*d**(max(row - t, 0))
        crrTree[row, 0] = max(x * St - x * K, 0)

    for col in range(t-1, -1, -1):
        for row in range(0, col*2+1):

            # move backwards from previous prices
            Su = crrTree[row,  0]
            Sm = crrTree[row + 1, 0]
            Sd = crrTree[row + 2, 0]
            # Calcuate price on tree
            continuation = math.exp(-r * dt) * (pu * Su + pm * Sm + pd * Sd)

            # Determine price at current node
            crrTree[row, 0] = continuation

    return crrTree[0, 0]


# S  : spot price
# K  : strike
# r  : riskless rate
# T  : maturity (in yrs.)
# t  : number of steps
# v  : annualized volatility
# c_p  : True, False

# r = 0.0416
# v = 0.5259
# T = 1
# S = 90.79  # stock price
# K = 280  # strike price
# # t = 1


# d1 = '2022/11/05'
# d2 = '2023/09/15'
# d1 = dt.strptime(d1, r'%Y/%m/%d')
# d2 = dt.strptime(d2, r'%Y/%m/%d')
# d = (d2 - d1).days/365
# T = d

# lst = []
# for i in range(1, t):
#     a = crr_trinomial_tree(S, K, r, T, i, v, type='call')
#     lst.append(a)


# plt.plot(lst)
# plt.xticks([x for x in range(1, t)])
# plt.show()
