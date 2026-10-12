"""
dea.py — Funciones de Análisis Envolvente de Datos (DEA) que usan oe3_dea_bootstrap.py,
oe2_malmquist.py y verificar_oe2_oe3.py. No se corre solo.

Convenciones
  X: matriz (n, m) de insumos   Y: matriz (n, s) de productos   (filas = universidades)
  Orientación al producto. Para cada universidad o se resuelve el programa de envolvente

      φ_o = máx φ   s.a.  Σ_j λ_j x_ij ≤ x_io        (cada insumo i)
                          Σ_j λ_j y_rj ≥ φ y_ro       (cada producto r)
                          Σ_j λ_j = 1                 (solo rendimientos variables, VRS/BCC)
                          λ_j ≥ 0

  φ_o ≥ 1 es cuánto podría multiplicar todos sus productos con el mismo insumo.
  Se reporta la EFICIENCIA δ_o = 1/φ_o ∈ (0, 1]: 1 = en la frontera; 0,80 = produce el 80 % de
  lo que podría (podría producir 1/0,80 = 1,25 veces lo actual).
  Cuando la universidad evaluada no está en la muestra de referencia (bootstrap, Malmquist
  entre años), δ puede ser mayor que 1.

Requiere: numpy, scipy (linprog con HiGHS).
"""
import numpy as np
from scipy.optimize import linprog


def phi_envolvente(x0, y0, Xref, Yref, vrs=True, metodo="highs"):
    """φ del programa de envolvente para el punto (x0, y0) contra la referencia (Xref, Yref).
    Devuelve (phi, lambdas)."""
    n, m = Xref.shape
    s = Yref.shape[1]
    c = np.zeros(n + 1)
    c[0] = -1.0                                            # maximizar φ
    A_ins = np.hstack([np.zeros((m, 1)), Xref.T])          # Σ λ x ≤ x0
    A_prod = np.hstack([np.asarray(y0).reshape(s, 1), -Yref.T])  # φ y0 − Σ λ y ≤ 0
    A_ub = np.vstack([A_ins, A_prod])
    b_ub = np.concatenate([x0, np.zeros(s)])
    A_eq = np.hstack([[0.0], np.ones(n)]).reshape(1, -1) if vrs else None
    b_eq = [1.0] if vrs else None
    r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                bounds=[(0, None)] * (n + 1), method=metodo)
    if r.status != 0:
        raise RuntimeError(f"El programa lineal no se resolvió: {r.message}")
    return r.x[0], r.x[1:]


def phi_multiplicadores(x0, y0, Xref, Yref, vrs=True, metodo="highs"):
    """φ por el programa DUAL (de multiplicadores). Debe dar lo mismo que phi_envolvente;
    se usa solo para verificar.
        mín v·x0 + v0   s.a.  u·y0 = 1;  v·x_j + v0 − u·y_j ≥ 0 ∀j;  u, v ≥ 0;  v0 libre (solo VRS)."""
    n, m = Xref.shape
    s = Yref.shape[1]
    # variables: [v (m), u (s), v0]
    c = np.concatenate([x0, np.zeros(s), [1.0 if vrs else 0.0]])
    A_ub = np.hstack([-Xref, Yref, -np.ones((n, 1)) if vrs else np.zeros((n, 1))])  # −(v·x + v0 − u·y) ≤ 0
    b_ub = np.zeros(n)
    A_eq = np.concatenate([np.zeros(m), y0, [0.0]]).reshape(1, -1)
    bounds = [(0, None)] * (m + s) + [(None, None) if vrs else (0, 0)]
    r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[1.0], bounds=bounds, method=metodo)
    if r.status != 0:
        raise RuntimeError(f"El programa dual no se resolvió: {r.message}")
    return r.fun


def metas(x0, y0, Xref, Yref, phi, vrs=True):
    """Segunda fase: con φ fijo, maximiza las holguras (normalizadas por el valor de la universidad)
    para obtener la meta completa de cada producto, no solo la expansión radial.
        máx Σ s_r / y_r0 + Σ e_i / x_i0   s.a.  Σ λ x + e = x0;  Σ λ y − s = φ y0;  Σ λ = 1 (VRS).
    Devuelve (metas de productos Σ λ y, holguras de productos s, holguras de insumos e, lambdas)."""
    n, m = Xref.shape
    s_ = Yref.shape[1]
    # variables: [λ (n), s (s_), e (m)]
    c = -np.concatenate([np.zeros(n), 1 / np.asarray(y0, float), 1 / np.asarray(x0, float)])
    A_eq = np.vstack([np.hstack([Xref.T, np.zeros((m, s_)), np.eye(m)]),
                      np.hstack([Yref.T, -np.eye(s_), np.zeros((s_, m))])])
    b_eq = np.concatenate([x0, phi * np.asarray(y0, float)])
    if vrs:
        A_eq = np.vstack([A_eq, np.concatenate([np.ones(n), np.zeros(s_ + m)])])
        b_eq = np.append(b_eq, 1.0)
    r = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * (n + s_ + m), method="highs")
    if r.status != 0:
        raise RuntimeError(f"La segunda fase no se resolvió: {r.message}")
    lam, hs, he = r.x[:n], r.x[n:n + s_], r.x[n + s_:]
    return lam @ Yref, hs, he, lam


def eficiencia(X, Y, Xref=None, Yref=None, vrs=True):
    """δ = 1/φ de cada fila de (X, Y) contra la referencia (por defecto, la misma muestra).
    Devuelve (delta, matriz de lambdas n × n_ref)."""
    Xref = X if Xref is None else Xref
    Yref = Y if Yref is None else Yref
    n = X.shape[0]
    delta = np.empty(n)
    lam = np.empty((n, Xref.shape[0]))
    for o in range(n):
        phi, l = phi_envolvente(X[o], Y[o], Xref, Yref, vrs=vrs)
        delta[o] = 1.0 / phi
        lam[o] = l
    return delta, lam


def bootstrap_simar_wilson(X, Y, B=2000, alfa=0.05, semilla=20261011, vrs=True):
    """Bootstrap suavizado homogéneo de Simar y Wilson (1998), versión orientada al producto.

    Se trabaja en la escala de Farrell φ = 1/δ ≥ 1, donde la reflexión en 1 no puede producir
    valores imposibles (en la escala δ ∈ (0,1] el ruido puede dar eficiencias negativas cuando
    son muy dispersas). Pasos, para b = 1..B:
      1. Remuestrear con reemplazo n valores β de los φ̂ estimados.
      2. Suavizar: φ̃ = β + h ε (ε ~ N(0,1)); si φ̃ < 1 se refleja: φ̃ = 2 − φ̃.
      3. Corregir la varianza: φ* = β̄ + (φ̃ − β̄) / sqrt(1 + h²/σ̂²)  (σ̂² = varianza de φ̂).
      4. Pseudo-muestra: mismos insumos; productos llevados a la frontera y contraídos:
         y*_j = y_j φ̂_j / φ*_j.
      5. Re-estimar φ̂*_b de cada universidad ORIGINAL contra la pseudo-muestra.
    Ancho de banda h: regla de Silverman sobre la muestra reflejada {φ̂, 2 − φ̂}:
      h = 0,9 · mín(σ, RIC/1,34) · n^(−1/5).
    Resultados (en φ y luego pasados a δ = 1/φ):
      sesgo φ = media_b(φ̂*_b) − φ̂;  φ corregido = φ̂ − sesgo;  δ corregida = 1/φ corregido;
      intervalo (1−α) de φ = [φ̂ − q_{1−α/2}(φ̂* − φ̂),  φ̂ − q_{α/2}(φ̂* − φ̂)], invertido para δ.
    """
    rng = np.random.default_rng(semilla)
    n = X.shape[0]
    d_hat, _ = eficiencia(X, Y, vrs=vrs)
    p_hat = 1 / d_hat
    refl = np.concatenate([p_hat, 2 - p_hat])
    ric = np.subtract(*np.percentile(refl, [75, 25]))
    h = 0.9 * min(refl.std(ddof=1), ric / 1.34) * n ** (-1 / 5)
    var = p_hat.var(ddof=1)
    boot = np.empty((B, n))
    for b in range(B):
        beta = rng.choice(p_hat, size=n, replace=True)
        pt = beta + h * rng.standard_normal(n)
        pt = np.where(pt < 1, 2 - pt, pt)
        p_star = beta.mean() + (pt - beta.mean()) / np.sqrt(1 + h ** 2 / var)
        Y_star = Y * (p_hat / p_star)[:, None]
        d_b, _ = eficiencia(X, Y, Xref=X, Yref=Y_star, vrs=vrs)
        boot[b] = 1 / d_b
    sesgo = boot.mean(axis=0) - p_hat
    p_corr = p_hat - sesgo
    dif = boot - p_hat
    p_lo = p_hat - np.quantile(dif, 1 - alfa / 2, axis=0)
    p_hi = p_hat - np.quantile(dif, alfa / 2, axis=0)
    return dict(delta=d_hat, phi=p_hat, sesgo_phi=sesgo, delta_corregida=1 / p_corr,
                ic_inf=1 / p_hi, ic_sup=1 / np.maximum(p_lo, 1e-9),
                var_boot_phi=boot.var(axis=0, ddof=1), h=h, B=B, semilla=semilla)
