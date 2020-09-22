import numpy as np
from numpy import linalg as la, random as rnd
from scipy.linalg import expm, logm

from pymanopt.manifolds.manifold import EuclideanEmbeddedSubmanifold
from pymanopt.tools.multi import multihconj, multiherm, multilog
from pymanopt.tools.multi import multiprod, multitransp


class HermitianPositiveDefinite(EuclideanEmbeddedSubmanifold):
    """Manifold of (n x n)^k complex Hermitian positive definite matrices.
    """
    def __init__(self, n, k=1):
        self._n = n
        self._k = k

        if k == 1:
            name = ("Manifold of Hermitian positive definite\
                    ({} x {}) matrices").format(n, n)
        else:
            name = "Product manifold of {} ({} x {}) matrices".format(k, n, n)
        dimension = 2 * int(k * n * (n + 1) / 2)
        super().__init__(name, dimension)

    def rand(self):
        # Generate eigenvalues between 1 and 2
        # (eigenvalues of a symmetric matrix are always real).
        d = np.ones((self._k, self._n, 1)) + rnd.rand(self._k, self._n, 1)

        # Generate an orthogonal matrix. Annoyingly qr decomp isn't
        # vectorized so need to use a for loop. Could be done using
        # svd but this is slower for bigger matrices.
        u = np.zeros((self._k, self._n, self._n), dtype=np.complex)
        for i in range(self._k):
            u[i], r = la.qr(
                rnd.randn(self._n, self._n)+1j*rnd.randn(self._n, self._n))

        if self._k == 1:
            return multiprod(u, d * multihconj(u))[0]
        return multiprod(u, d * multihconj(u))

    def randvec(self, x):
        k = self._k
        n = self._n
        if k == 1:
            u = multiherm(rnd.randn(n, n)+1j*rnd.randn(n, n))
        else:
            u = multiherm(rnd.randn(k, n, n)+1j*rnd.randn(k, n, n))
        return u / self.norm(x, u)

    def zerovec(self, x):
        k = self._k
        n = self._n
        if k != 1:
            return np.zeros((k, n, n), dtype=np.complex)
        return np.zeros((n, n), dtype=np.complex)

    def inner(self, x, u, v):
        return np.real(
            np.tensordot(la.solve(x, u), multitransp(la.solve(x, v)),
                         axes=x.ndim))

    def norm(self, x, u):
        # This implementation is as fast as np.linalg.solve_triangular and is
        # more stable, as the above solver tends to output non positive
        # definite results.
        c = la.cholesky(x)
        c_inv = la.inv(c)
        return np.real(
            la.norm(multiprod(multiprod(c_inv, u), multihconj(c_inv))))

    def proj(self, X, G):
        return multiherm(G)

    def egrad2rgrad(self, x, u):
        return multiprod(multiprod(x, multiherm(u)), x)

    def exp(self, x, u):
        x_inv_u = la.solve(x, u)
        if self._k > 1:
            e = np.zeros(np.shape(x), dtype=np.complex)
            for i in range(self._k):
                e[i] = expm(x_inv_u[i])
        else:
            e = expm(x_inv_u)
        return multiherm(multiprod(x, e))

    retr = exp

    def log(self, x, y):
        x_inv_y = la.solve(x, y)
        if self._k > 1:
            log = np.zeros(np.shape(x), dtype=np.complex)
            for i in range(self._k):
                log[i] = logm(x_inv_y[i])
        else:
            log = logm(x_inv_y)
        return multiherm(multiprod(x, log))

    def transp(self, x1, x2, d):
        return d

    def dist(self, x, y):
        c = la.cholesky(x)
        c_inv = la.inv(c)
        logm = multilog(multiprod(multiprod(c_inv, y), multihconj(c_inv)),
                        pos_def=True)
        return np.real(la.norm(logm))