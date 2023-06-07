import numpy as np

mu = 0.1
n = 1780*2

T = 10
M = 1

sigma = 0.3

dt = T/n

def new_prices(s0):
    st = np.exp((mu - sigma**2/2) * dt + sigma * np.random.normal(0, np.sqrt(dt), size=(M, n))).T
    st = np.vstack([np.ones(M), st])

    return [i[0] for i in (s0 * st.cumprod(axis=0))]

print(new_prices(1))