import math
import physics_engine as engine

L, x = 1000.0, 500.0
Fa = Fm = 500.0
Ta, Tm = 10000.0, 40000.0
fos, theta_max = 2.0, 1.0
ka, kb, kc = 0.80, 1.0, 0.868
Kt = Kts = 1.0
q = qs = 0.8
Sut, Syt, G = 600.0, 380.0, 79e3
Se = 0.5 * Sut * ka * kb * kc
Ma, Mm = Fa * x, Fm * x
S = math.sqrt(4 * ((Ma / Se) ** 2 + (Mm / Syt) ** 2) + 3 * ((Ta / Se) ** 2 + (Tm / Syt) ** 2))
d_strength_hand = (16 * fos * S / math.pi) ** (1 / 3)
d_rigidity_hand = (584 * (Ta + Tm) * x / (G * theta_max)) ** 0.25

loads = [{'x': x, 'F_a': Fa, 'F_m': Fm, 'T_a': Ta, 'T_m': Tm, 'M_a': 0.0, 'M_m': 0.0}]
r = engine.compute_shaft_design(L, loads, "Fixed", "Free", fos, 80.0, theta_max,
                                "C45 Carbon Steel", ka, kb, kc, Kt, Kts, q, qs)
print(f"cantilever d_strength hand={d_strength_hand:.4f} engine={r['d_strength']:.4f}")
print(f"cantilever d_rigidity hand={d_rigidity_hand:.4f} engine={r['d_rigidity']:.4f}")
assert abs(d_strength_hand - r['d_strength']) < 1e-6
assert abs(d_rigidity_hand - r['d_rigidity']) < 1e-6
assert r['critical_x'] == 0.0

s = engine._State(1000.0, [{'x': 400.0, 'M_a': 1e5}], "Pin", "Roller", 'F_a', 'M_a', 'T_a')
assert abs(s.moment(400.0, '-') - 40000.0) < 1e-6
assert abs(s.moment(400.0, '+') - 60000.0) < 1e-6

P, Lp = 1000.0, 1000.0
st = engine._State(Lp, [{'x': 500.0, 'F_a': P}], "Fixed", "Roller", 'F_a', 'M_a', 'T_a')
assert abs(st.R2 / P - 5 / 16) < 1e-9
assert abs(st.moment(0.0, '+') / (P * Lp) - 3 / 16) < 1e-9
assert abs(st.moment(500.0, '-') / (P * Lp) - 5 / 32) < 1e-9

for sl, sr in (("Pin", "Free"), ("Roller", "Free")):
    try:
        engine.compute_shaft_design(L, loads, sl, sr, fos, 80.0, theta_max,
                                    "C45 Carbon Steel", ka, kb, kc, Kt, Kts, q, qs)
        raise SystemExit("unstable case was accepted")
    except ValueError:
        pass

print("ALL CHECKS PASSED")
