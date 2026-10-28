"""Does a Markov chain forget where it started? (Marginalia 01, gideonong.me/learning/marginalia/)

Companion script: the same exact calculations as the page, in NumPy. It runs top to bottom as a
plain script, and as a Colab notebook (the "# %%" markers become cells).
Text, figures and code: CC BY-SA 4.0, Gideon A. Ong.
"""

# %% [markdown]
# ## 1. The two-state chain
# A machine checked once per shift: up → down with probability `a`, down → up with probability `b`.
# Rows of `P` are "from up" and "from down".

# %%
import numpy as np
import matplotlib.pyplot as plt


def chain(a, b):
    """Transition matrix, availability pi_up = b/(a+b) and the memory factor lam = 1 - a - b."""
    P = np.array([[1 - a, a], [b, 1 - b]])
    lam = 1 - a - b
    pi_up = b / (a + b) if a + b > 0 else float("nan")
    return P, pi_up, lam


a, b = 0.05, 0.30
P, pi_up, lam = chain(a, b)
print(f"a = {a}, b = {b}: availability pi_up = {pi_up:.4f}, lambda = {lam:.2f}")
print(f"mean up-time MTTF = 1/a = {1 / a:.1f} shifts, MTTR = 1/b = {1 / b:.2f} shifts, "
      f"MTTF/(MTTF+MTTR) = {(1 / a) / (1 / a + 1 / b):.4f}")

# %% [markdown]
# ## 2. The settling rule
# |P(up at n) − pi_up| = |lambda|^n · |P(up at 0) − pi_up|, so the number of steps to get within
# eps of the long-run value from the worst start is ln(eps / gap0) / ln|lambda|.

# %%
def steps_to_settle(a, b, eps=0.01):
    _, pi_up, lam = chain(a, b)
    gap0 = max(pi_up, 1 - pi_up)
    if abs(lam) < 1e-12:
        return 1
    if abs(lam) >= 1:
        return float("inf")
    return max(0, int(np.ceil(np.log(eps / gap0) / np.log(abs(lam)))))


print("steps to within 0.01:", steps_to_settle(a, b))
print("time constant tau = -1/ln|lambda| =", round(-1 / np.log(abs(lam)), 3), "steps")

# Check against matrix powers: row 0 of P^n starts up, row 1 starts down.
for n in [1, 5, 10, 11]:
    Pn = np.linalg.matrix_power(P, n)
    print(f"n = {n:2d}: P(up | start up) = {Pn[0, 0]:.5f}, P(up | start down) = {Pn[1, 0]:.5f}")

# %% [markdown]
# ## 3. The closed form P^n = Pi + lambda^n (I − Pi)
# `Pi` has both rows equal to the stationary distribution. Check it numerically.

# %%
Pi = np.array([[pi_up, 1 - pi_up], [pi_up, 1 - pi_up]])
I = np.eye(2)
for n in [1, 3, 20]:
    err = np.abs(np.linalg.matrix_power(P, n) - (Pi + lam ** n * (I - Pi))).max()
    print(f"n = {n:2d}: largest difference from the closed form = {err:.2e}")

# %% [markdown]
# ## 4. The pictures: settling, and the gap on a log scale

# %%
def p_path(p0, a, b, N=30):
    lam = 1 - a - b
    out = [p0]
    for _ in range(N):
        out.append(lam * out[-1] + b)
    return np.array(out)


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
for (a_, b_, name) in [(0.05, 0.30, "machine"), (0.9, 0.8, "rings")]:
    _, pi_, lam_ = chain(a_, b_)
    up, dn = p_path(1, a_, b_), p_path(0, a_, b_)
    n = np.arange(len(up))
    ax1.plot(n, up, label=f"{name}: start up")
    ax1.plot(n, dn, "--", label=f"{name}: start down")
    ax2.semilogy(n, np.abs(dn - pi_), "o", ms=3, label=f"{name}: exact gap")
    ax2.semilogy(n, pi_ * abs(lam_) ** n, ":", label=f"{name}: |lambda|^n x gap0")
ax1.set(xlabel="step n", ylabel="P(up at step n)")
ax2.set(xlabel="step n", ylabel="|P(up) - pi_up|, start down", ylim=(1e-6, 1))
ax1.legend(fontsize=8)
ax2.legend(fontsize=8)
fig.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Time fraction versus limit: the flip chain (a = b = 1)
# P(up at n) alternates 1, 0, 1, 0, but the fraction of time up converges to 1/2.

# %%
up = p_path(1, 1.0, 1.0, N=40)
running = np.cumsum(up) / np.arange(1, len(up) + 1)
print("P(up at n), n = 0..7:      ", up[:8])
print("fraction of time up so far:", np.round(running[:8], 3), "...", round(running[-1], 3))

# %% [markdown]
# ## 6. Bigger chains: the second-largest eigenvalue modulus sets the rate
# A 3-state example made up for this script. |lambda_2| plays the role of |lambda|.

# %%
Q = np.array([[0.90, 0.08, 0.02],
              [0.10, 0.80, 0.10],
              [0.05, 0.25, 0.70]])
mods = np.sort(np.abs(np.linalg.eigvals(Q)))[::-1]
print("eigenvalue moduli:", np.round(mods, 4))
w, v = np.linalg.eig(Q.T)
pi = np.real(v[:, np.argmin(np.abs(w - 1))])
pi = pi / pi.sum()
for n in [5, 10, 20, 40]:
    dist = np.abs(np.linalg.matrix_power(Q, n) - pi).max()
    print(f"n = {n:2d}: max |Q^n - Pi| = {dist:.2e}   |lambda_2|^n = {mods[1] ** n:.2e}")
