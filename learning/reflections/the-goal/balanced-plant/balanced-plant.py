"""
# The Balanced Plant Theorem — Reflections on The Goal

The reflection page: https://gideonong.me/learning/reflections/the-goal/balanced-plant/

Simulations and exact solutions behind the page: the dice game, M/M/1 at utilization 1,
Kingman's formula, finite-buffer serial lines, the bowl phenomenon, protective capacity,
and why naive confidence intervals fail on queue output.

Run it:
  * Google Colab: use "Open in Colab" on the page (or upload this file). Everything needed
    is preinstalled. Run the cells top to bottom (about 10 seconds).
  * Your own PC:  pip install numpy scipy matplotlib   then   python -X utf8 balanced-plant.py
    (-X utf8 because the printouts use ≈, ± and −, which a Windows console may not encode)

All data are simulated; each section states its model.
"""

# %% [markdown]
# ## 1. Library

# %%
import numpy as np, matplotlib.pyplot as plt
from scipy.optimize import curve_fit
plt.rcParams.update({'figure.dpi':110,'axes.grid':True,'grid.alpha':.3})

"""Serial production line tools: exact CTMC throughput (exponential stations,
finite buffers, blocking after service) and a discrete-event simulator for
general (gamma) processing times. Used to verify the numbers in the explainer
and as the core of the Colab notebook."""
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve

W, B, I = 0, 1, 2  # working, blocked (holding a finished part), idle (starved)


def _settle(st, buf, b):
    st, buf = list(st), list(buf)
    n = len(st)
    changed = True
    while changed:
        changed = False
        for i in range(n - 1):
            if st[i] == B:
                if st[i + 1] == I and buf[i] == 0:
                    st[i + 1] = W
                elif buf[i] < b:
                    buf[i] += 1
                else:
                    continue
                st[i] = W if i == 0 else I
                changed = True
        for j in range(1, n):
            if st[j] == I and buf[j - 1] > 0:
                buf[j - 1] -= 1
                st[j] = W
                changed = True
    return tuple(st), tuple(buf)


def exact_throughput(mu, b):
    """Exact long-run throughput of a serial line of exponential stations with
    rates mu[0..N-1], buffer capacity b between each pair (excluding the
    machines themselves), unlimited raw material, blocking after service."""
    n = len(mu)
    start = _settle((W,) + (I,) * (n - 1), (0,) * (n - 1), b)
    index, states, frontier = {start: 0}, [start], [start]
    trans = []
    while frontier:
        s = frontier.pop()
        st, buf = s
        for i in range(n):
            if st[i] != W:
                continue
            nst = list(st)
            nst[i] = I if i == n - 1 else B
            t = _settle(nst, buf, b)
            if t not in index:
                index[t] = len(states)
                states.append(t)
                frontier.append(t)
            trans.append((index[s], index[t], mu[i]))
    m = len(states)
    Q = lil_matrix((m, m))
    for a, c, r in trans:
        if a != c:
            Q[a, c] += r
            Q[a, a] -= r
    A = Q.T.tocsr().tolil()
    A[0, :] = np.ones(m)          # replace one balance equation by normalization
    rhs = np.zeros(m); rhs[0] = 1
    pi = spsolve(csr_matrix(A), rhs)
    th = sum(p * mu[-1] for p, (st, _) in zip(pi, states) if st[-1] == W)
    wip = sum(p * (sum(buf) + sum(1 for x in st[1:] if x != I) + 1)
              for p, (st, buf) in zip(pi, states))
    return th, wip, m


def gamma_sampler(rng, mean, scv):
    """Processing-time sampler with given mean and squared coefficient of
    variation (scv = variance / mean^2). scv=0 -> deterministic, 1 -> exponential."""
    if scv == 0:
        return lambda size: np.full(size, mean)
    k = 1.0 / scv
    return lambda size: rng.gamma(k, mean / k, size)


def simulate_line(means, scvs, b, n_jobs=200_000, seed=0, warmup=0.1):
    """Simulate a serial line (unlimited raw material, blocking after service,
    buffer capacity b between stations; b=None means unlimited).
    Uses the departure-time recursion for tandem lines with blocking:
        D[i][k] = max( max(D[i-1][k], D[i][k-1]) + S[i][k],  D[i+1][k-b-1] )
    Returns throughput and average WIP (Little's law: WIP = TH * flow time)."""
    rng = np.random.default_rng(seed)
    n = len(means)
    S = np.vstack([gamma_sampler(rng, m, c)(n_jobs) for m, c in zip(means, scvs)])
    D = np.zeros((n, n_jobs))
    lag = None if b is None else b + 1
    for k in range(n_jobs):
        for i in range(n):
            start = D[i, k - 1] if k > 0 else 0.0
            if i > 0:
                start = max(start, D[i - 1, k])
            done = start + S[i, k]
            if lag is not None and i < n - 1 and k - lag >= 0:
                done = max(done, D[i + 1, k - lag])   # blocked until space downstream
            D[i, k] = done
    # job k enters the line when station 0 starts it
    start0 = np.concatenate([[0.0], D[0, :-1]])
    k0 = int(warmup * n_jobs)
    th = (n_jobs - 1 - k0) / (D[-1, -1] - D[-1, k0])
    flow = np.mean(D[-1, k0:] - start0[k0:])
    return th, th * flow

# %%
# Sanity checks: two balanced stations give (b+2)/(b+3); three with no buffer give 22/39
for b in range(4):
    th, wip, m = exact_throughput([1, 1], b)
    print(f"b={b}: exact {th:.5f}, formula {(b+2)/(b+3):.5f}, chain states {m}")
print("3 stations, b=0:", exact_throughput([1,1,1], 0)[0], "vs 22/39 =", 22/39)

# %% [markdown]
# ## 2. The dice game
# Each station moves `min(roll, matches in its bowl)`; station 1 draws from an unlimited box. Material is conserved, so on average the output shortfall versus 3.5 per round equals the WIP left in bowls (in one game the two differ by station 1's release noise). We fit `WIP(t) = c·t^p` with **p free** to check the √t prediction instead of assuming it. Expect p a little above ½ over a few hundred rounds: with several stations in series the √t regime arrives slowly. Try `rounds=4000, games=1000`.

# %%
rng = np.random.default_rng(1)
def dice_games(n_st=5, rounds=400, games=5000, low=1, high=6):
    inv = np.zeros((games, n_st)); out = np.zeros(games)
    wip = np.zeros((games, rounds + 1)); cum = np.zeros((games, rounds + 1))
    for r in range(1, rounds + 1):
        for i in range(n_st):
            x = rng.integers(low, high + 1, games)
            mv = x if i == 0 else np.minimum(x, inv[:, i])
            if i > 0: inv[:, i] -= mv
            if i < n_st - 1: inv[:, i + 1] += mv
            else: out += mv
        wip[:, r] = inv.sum(1); cum[:, r] = out
    return cum.mean(0), wip.mean(0)

t = np.arange(401)
cum, wip = dice_games()
(c, p), cov = curve_fit(lambda t, c, p: c * t**p, t[10:], wip[10:], p0=(1, .5))
print(f"fit WIP ≈ {c:.2f}·t^{p:.3f}  (p ± {np.sqrt(cov[1,1]):.3f});  shortfall − WIP at end (0 up to Monte Carlo noise) = {3.5*400 - cum[-1] - wip[-1]:.3f}")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].plot(t, 3.5*t, '--', label='plan 3.5/round'); ax[0].plot(t, cum, label='mean output'); ax[0].legend(); ax[0].set_xlabel('round')
ax[1].plot(t, wip, label='mean WIP'); ax[1].plot(t, c*t**p, '--', label=f'{c:.2f}·t^{p:.2f}'); ax[1].legend(); ax[1].set_xlabel('round')
plt.show()
# Try: low=3, high=4 (less variability), or n_st=10. How do c and p change?

# %% [markdown]
# ## 3. M/M/1 at ρ = 1
# With λ = μ = 1 the queue is a reflected random walk with no drift. Theory (CLT + Lévy's theorem): E[N(t)] ≈ 2√(λt/π).

# %%
def mm1_path_grid(lam, mu, T, grid, rng):
    n_ev = rng.poisson((lam + mu) * T * 1.1) + 50
    times = np.cumsum(rng.exponential(1/(lam+mu), n_ev))
    steps = np.where(rng.random(n_ev) < lam/(lam+mu), 1, -1)
    n = np.empty(n_ev); x = 0
    for k, s in enumerate(steps):      # reflection at 0
        x = max(0, x + s); n[k] = x
    idx = np.searchsorted(times, grid, side='right') - 1
    return np.where(idx >= 0, n[np.clip(idx, 0, None)], 0)

T = 2000; grid = np.linspace(0, T, 201); rng = np.random.default_rng(2)
paths = np.array([mm1_path_grid(1, 1, T, grid, rng) for _ in range(500)])
plt.figure(figsize=(7, 3.8))
for k in range(4): plt.plot(grid, paths[k], lw=.8, alpha=.5)
plt.plot(grid, paths.mean(0), lw=2.5, label='mean of 500')
plt.plot(grid, 2*np.sqrt(grid/np.pi), 'k--', label='2√(t/π)'); plt.legend(); plt.xlabel('t'); plt.ylabel('N(t)'); plt.show()

# %% [markdown]
# ## 4. Kingman (VUT) vs. simulation
# Lindley's recursion W₍ₖ₊₁₎ = max(0, Wₖ + Sₖ − Aₖ₊₁) has a closed form when the queue starts empty: Wₖ = Xₖ − min(0, X₁, …, Xₖ), where X is the running sum of Sⱼ − Aⱼ₊₁. That makes it fully vectorized.

# %%
def gamma_times(rng, mean, scv, n):
    return np.full(n, mean) if scv == 0 else rng.gamma(1/scv, mean*scv, n)

def lindley_mean(u, ca2, cs2, n=2_000_000, rng=np.random.default_rng(3)):
    X = np.cumsum(gamma_times(rng, 1, cs2, n) - gamma_times(rng, 1/u, ca2, n))
    W = X - np.minimum(np.minimum.accumulate(X), 0)
    return W[n//20:].mean()

us = np.array([.3, .5, .7, .8, .85, .9, .95]); uu = np.linspace(.01, .97, 200)
plt.figure(figsize=(7, 4))
for (ca2, cs2), col in zip([(1, 1), (1, .25), (.25, .25), (0, 1)], ['C0', 'C1', 'C2', 'C3']):
    V = (ca2 + cs2) / 2
    plt.plot(uu, V*uu/(1-uu), col, label=f'c²a={ca2}, c²s={cs2}')
    plt.plot(us, [lindley_mean(u, ca2, cs2) for u in us], 'o', color=col)
plt.ylim(0, 25); plt.xlabel('utilization u'); plt.ylabel('Wq / tₑ'); plt.legend(); plt.title('lines: Kingman, dots: simulation'); plt.show()

# %% [markdown]
# ## 5. Finite buffers
# Exact chain (exponential, c² = 1) vs. the line simulator, then the simulator at c² = 0.25 to see how much lower variability helps.
# `simulate_line` uses the departure-time recursion for blocking-after-service lines; it's a plain Python loop, so keep `n_jobs` around 10⁵.

# %%
bs = range(0, 7); N = 4
exact = [exact_throughput([1]*N, b)[0] for b in bs]
sim1  = [simulate_line([1]*N, [1]*N, b, 60_000, seed=b)[0] for b in bs]
sim25 = [simulate_line([1]*N, [.25]*N, b, 60_000, seed=b)[0] for b in bs]
plt.figure(figsize=(7, 3.8))
plt.plot(bs, exact, 'o-', label='exact, c²=1'); plt.plot(bs, sim1, 'x', ms=9, label='simulated, c²=1')
plt.plot(bs, sim25, 's-', label='simulated, c²=0.25'); plt.axhline(1, ls='--', c='gray')
plt.xlabel('buffer slots b'); plt.ylabel('throughput ÷ demand'); plt.title(f'{N} balanced stations'); plt.legend(); plt.show()

# %% [markdown]
# ## 6. The bowl phenomenon (exact)
# Three exponential stations, total mean work 3; vary the middle station's share.

# %%
xs = np.linspace(.8, 1.2, 33)
plt.figure(figsize=(7, 3.8))
for b in [0, 1, 3]:
    th = np.array([exact_throughput([2/(3-x), 1/x, 2/(3-x)], b)[0] for x in xs])
    plt.plot(xs, 100*(th/th[16] - 1), label=f'b={b}, best x={xs[th.argmax()]:.3f}')
plt.axvline(1, ls='--', c='gray'); plt.xlabel("middle station's mean time"); plt.ylabel('% vs balanced'); plt.legend(); plt.show()

# %% [markdown]
# ## 7. Protective capacity
# Goldratt's fix: keep the bottleneck at demand, give every other station spare capacity. Here station 3 of 5 is the bottleneck (rate 1); the others get rate 1 + m.

# %%
ms = [0, .05, .1, .2, .3, .5]
for b in [0, 2]:
    th = [exact_throughput([1+m, 1+m, 1, 1+m, 1+m], b)[0] for m in ms]
    print(f"b={b}: " + ", ".join(f"m={m:.2f}→{t:.3f}" for m, t in zip(ms, th)))
# Compare with the bowl: a 10% capacity margin vs. a 0.5% work reshuffle.

# %% [markdown]
# ## 8. Why naive confidence intervals fail on queue output
# Consecutive waits are strongly autocorrelated, so treating 10⁵ waits as independent badly understates the standard error. **Batch means**: cut the run into ~30 big batches, treat the batch averages as roughly independent.
# Same lesson as residual plots: check the independence assumption before trusting a standard error.

# %%
rng = np.random.default_rng(4); u = 0.9; n = 200_000
X = np.cumsum(rng.exponential(1, n) - rng.exponential(1/u, n))
W = (X - np.minimum(np.minimum.accumulate(X), 0))[n//20:]
naive_se = W.std(ddof=1) / np.sqrt(len(W))
batches = W[:len(W)//30*30].reshape(30, -1).mean(1); bm_se = batches.std(ddof=1) / np.sqrt(30)
print(f"mean wait {W.mean():.2f} (theory {u/(1-u):.2f})")
print(f"naive SE {naive_se:.3f}  vs  batch-means SE {bm_se:.3f}  (ratio {bm_se/naive_se:.0f}×)")
lags = np.arange(0, 2000, 20); W0 = W - W.mean()
acf = [np.dot(W0[:-l or None], W0[l:]) / np.dot(W0, W0) for l in lags]
plt.figure(figsize=(7, 3)); plt.plot(lags, acf); plt.xlabel('lag (jobs)'); plt.ylabel('autocorrelation'); plt.show()
