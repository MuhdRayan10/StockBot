import numpy as np

mu = 0.1
n = 17280

T = 1
M = 1

sigma = 0.3

dt = T/n

def new_price(s0):
    st = np.exp((mu - sigma**2/2) * dt + sigma * np.random.normal(0, np.sqrt(dt), size=(M, n))).T
    st = np.vstack([np.ones(M), st])

    return round((s0 * st.cumprod(axis=0))[1][0], 2)



