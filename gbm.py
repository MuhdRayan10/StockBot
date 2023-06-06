import matplotlib.pyplot as plt
import numpy as np

mu = 0.1
n = 100

T = 1 
M = 2

s0 = 100
sigma = 0.3

dt = T/n

st = np.exp((mu - sigma**2/2) * dt + sigma * np.random.normal(0, np.sqrt(dt), size=(M, n))).T
st = np.vstack([np.ones(M), st])

st = s0 * st.cumprod(axis=0)

time = np.linspace(0, T, n+1)
tt = np.full(shape=(M,n+1), fill_value=time).T

plt.plot(tt, st)
plt.xlabel("Years $(t)$")
plt.ylabel("Stock Price $(S_t)$")

plt.title("Realizations of Geometric Brownian Motion\n $dS_t = \mu S_t dt + \sigma S_t dW_t$\n $S_0 = {0}, \mu = {1}, \sigma = {2}$".format(s0, mu, sigma))
plt.show()


