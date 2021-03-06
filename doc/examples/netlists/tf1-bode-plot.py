from lcapy import s, j, pi, f, LaplaceDomainTransferFunction
from matplotlib.pyplot import savefig
from numpy import logspace

H = LaplaceDomainTransferFunction((s - 2) * (s + 3) / (s * (s - 2 * j) * (s + 2 * j)))

A = H(j * 2 * pi * f)

fv = logspace(-1, 4, 400)
A.plot(fv, log_scale=True)


savefig('tf1-bode-plot.png')
