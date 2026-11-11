import math

STANDARD_DIAMETERS = [
    10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 32, 35, 40, 45, 50,
    55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140, 150
]

MATERIALS_DB = {
    "C45 Carbon Steel": {
        "cat": "Steel", "Sut": 600, "Syt": 380, "G": 79e3,
        "verified": True, "src": "Course values; Se' = 0.5*Sut (Shigley rule)"},
    "40Cr1 Alloy Steel": {
        "cat": "Steel", "Sut": 700, "Syt": 460, "G": 80e3,
        "verified": True, "src": "Course values; Se' = 0.5*Sut (Shigley rule)"},
    "4140 High Tensile Steel": {
        "cat": "Steel", "Sut": 1000, "Syt": 750, "G": 80e3,
        "verified": True, "src": "Course values; Se' = 0.5*Sut (Shigley rule)"},
    "Stainless Steel 304": {
        "cat": "Steel", "Sut": 515, "Syt": 205, "G": 77e3, "Se_prime": 180,
        "verified": True,
        "src": "Se' = 0.35*Sut at 1e7 cycles (Stainless Structurals 304/304L data sheet); "
               "G = 77 GPa (MatWeb 304); Sut/Syt = ASTM minimum"},
    "Aluminium 6061-T6": {
        "cat": "Aluminium", "Sut": 310, "Syt": 276, "G": 26e3, "Se_prime": 96.5,
        "verified": True,
        "src": "Se' = 96.5 MPa, 5e8 cycles, R.R. Moore (ASM/MatWeb 6061-T6 data sheet, "
               "aerospacemetals.com). Sut, Syt, G are typical values - confirm on the same sheet"},
    "Aluminium 7075-T6": {
        "cat": "Aluminium", "Sut": 572, "Syt": 503, "G": 26.9e3, "Se_prime": 159,
        "verified": True,
        "src": "ASM/MatWeb 7075-T6 data sheet: Sut 572, Syt 503, G 26.9 GPa, "
               "Se' = 159 MPa at 5e8 cycles, R.R. Moore"},
    "Brass C36000 (half-hard)": {
        "cat": "Copper", "Sut": 414, "Syt": 290, "G": 39e3, "Se_prime": 138,
        "verified": False,
        "src": "Sut/Syt = CDA typical, half-hard rod 12.7-25.4 mm; G = 39 GPa (ASM Handbook "
               "Vol.2 via MakeItFrom). Se' = 138 MPa is listed for H04 (hard) rod by National "
               "Bronze, not half-hard; cycle count not stated. CONFIRM"},
    "Titanium Ti-6Al-4V": {
        "cat": "Titanium", "Sut": 950, "Syt": 880, "G": 44e3, "Se_prime": 510,
        "verified": True,
        "src": "ASM/MatWeb Ti-6Al-4V Grade 5 annealed: Sut 950, Syt 880, G 44 GPa, "
               "Se' = 510 MPa unnotched at 1e7 cycles (test type not stated)"},
}

SURFACE_FACTORS = {
    "Ground": 0.92,
    "Machined / Cold-Drawn": 0.80,
    "Hot-Rolled": 0.60,
    "As-Forged": 0.45,
    "Custom": None
}

RELIABILITY_FACTORS = {
    "50% (kc = 1.000)": 1.000,
    "90% (kc = 0.897)": 0.897,
    "95% (kc = 0.868)": 0.868,
    "99% (kc = 0.814)": 0.814,
    "99.9% (kc = 0.753)": 0.753,
    "Custom": None
}

EPS = 1e-9

def _se_prime(mat):
    if "Se_prime" in mat:
        return mat["Se_prime"]
    return 0.5 * mat["Sut"] if mat["Sut"] <= 1400 else 700.0

SURFACE_AB = {
    "Ground": (1.58, -0.085),
    "Machined / Cold-Drawn": (4.51, -0.265),
    "Hot-Rolled": (57.7, -0.718),
    "As-Forged": (272.0, -0.995),
}

def surface_factor(surface, Sut):
    a, b = SURFACE_AB[surface]
    return min(1.0, a * Sut ** b)

KT_ESTIMATES = {
    "None (plain shaft)": (1.0, 1.0),
    "Shoulder fillet - sharp (r/d = 0.02)": (2.7, 2.2),
    "Shoulder fillet - well rounded (r/d = 0.1)": (1.7, 1.5),
    "End-milled keyseat": (2.14, 3.0),
    "Retaining ring groove": (5.0, 3.0),
}

def notch_sensitivity(Sut, r_mm, shear=False):
    if r_mm <= 0:
        raise ValueError("Notch radius must be positive.")
    if shear:
        sqrt_a = 0.958 - 1.83e-3 * Sut + 1.43e-6 * Sut ** 2 - 4.11e-10 * Sut ** 3
    else:
        sqrt_a = 1.24 - 2.25e-3 * Sut + 1.60e-6 * Sut ** 2 - 4.11e-10 * Sut ** 3
    return 1.0 / (1.0 + sqrt_a / math.sqrt(r_mm))

def size_factor(d):
    if d < 2.79:
        return 1.0
    if d <= 51.0:
        return 1.24 * d ** -0.107
    return 1.51 * d ** -0.157

def calculate_fatigue_factors(mat, ka, kb, kc, Kt, Kts, q, q_s):
    Se = _se_prime(mat) * ka * kb * kc
    Kf = 1.0 + q * (Kt - 1.0)
    Kfs = 1.0 + q_s * (Kts - 1.0)
    return Se, Kf, Kfs

SUPPORT_OPTIONS_LEFT = ("Pin", "Roller", "Fixed")
SUPPORT_OPTIONS_RIGHT = ("Roller", "Pin", "Free")

def _mode(support_left, support_right):
    left_fixed, right_fixed = support_left == "Fixed", support_right == "Fixed"
    left_free, right_free = support_left == "Free", support_right == "Free"
    if (left_free and right_free):
        raise ValueError("Both ends are free: the shaft has no support.")
    if left_fixed and right_free:
        return "cant_left"
    if left_free and right_fixed:
        return "cant_right"
    if left_fixed and right_fixed:
        return "fixed_fixed"
    if left_fixed:
        return "propped"
    if right_free or left_free:
        raise ValueError(
            f"Unstable support combination ({support_left} - {support_right}): a single "
            "pin/roller cannot hold the shaft. Use Fixed - Free, or supports at both ends.")
    return "simple"

class _State:

    def __init__(self, length, loads, sl, sr, f_key, m_key, t_key):
        self.L = length
        self.loads = loads
        self.sl, self.sr = sl, sr
        self.f_key, self.m_key, self.t_key = f_key, m_key, t_key
        self.mode = _mode(sl, sr)
        if self.mode == "fixed_fixed":
            self.mode = "simple"

        F = sum(l.get(f_key, 0.0) for l in loads)
        mom = sum(l.get(f_key, 0.0) * l['x'] + l.get(m_key, 0.0) for l in loads)
        self.total_T = sum(l.get(t_key, 0.0) for l in loads)

        if self.mode == "cant_left":
            self.R1, self.R2 = F, 0.0
        elif self.mode == "cant_right":
            self.R1, self.R2 = 0.0, F
        elif self.mode == "propped":
            L = length
            num = sum(l.get(f_key, 0.0) * l['x'] ** 2 * (3 * L - l['x']) / 6.0
                      + l.get(m_key, 0.0) * l['x'] * (2 * L - l['x']) / 2.0 for l in loads)
            self.R2 = 3.0 * num / L ** 3
            self.R1 = F - self.R2
        else:
            self.R2 = mom / length
            self.R1 = F - self.R2

        self.T_R1 = self.total_T if sl == "Fixed" else 0.0
        self.T_R2 = self.total_T if (sr == "Fixed" and sl != "Fixed") else 0.0

    def _left(self, x, side):
        for l in self.loads:
            xi = l['x']
            if xi < x - EPS or (abs(xi - x) <= EPS and side == '+'):
                yield l

    def _right(self, x, side):
        for l in self.loads:
            xi = l['x']
            if xi > x + EPS or (abs(xi - x) <= EPS and side == '-'):
                yield l

    def moment(self, x, side):
        f, m = self.f_key, self.m_key
        if self.mode in ("cant_left", "propped"):
            M = self.R2 * (self.L - x) - sum(
                l.get(f, 0.0) * (l['x'] - x) + l.get(m, 0.0) for l in self._right(x, side))
        else:
            M = self.R1 * x - sum(l.get(f, 0.0) * (x - l['x']) - l.get(m, 0.0)
                                  for l in self._left(x, side))
        return abs(M)

    def torque(self, x, side):
        cum = sum(l.get(self.t_key, 0.0) for l in self._left(x, side))
        left_reaction = -self.total_T if self.sl == "Fixed" else 0.0
        return abs(cum + left_reaction)

def _validate(length, loads, fos, theta_max, d_max):
    if length <= 0:
        raise ValueError("Shaft length must be positive.")
    if fos <= 0:
        raise ValueError("Factor of safety must be positive.")
    if d_max <= 0:
        raise ValueError("Maximum diameter must be positive.")
    if theta_max <= 0:
        raise ValueError("Maximum angle of twist must be positive.")
    if not loads:
        raise ValueError("Add at least one load.")
    for i, l in enumerate(loads, start=1):
        if not (0.0 <= l['x'] <= length):
            raise ValueError(
                f"Load row {i}: position x = {l['x']} is outside the shaft (0 to {length}).")

def _sections(length, loads):
    pts = [(0.0, '+'), (length, '-')]
    for l in loads:
        pts.append((l['x'], '-'))
        pts.append((l['x'], '+'))
    return pts

def solve_reactions_and_moments(length, loads, support_left, support_right):
    sa = _State(length, loads, support_left, support_right, 'F_a', 'M_a', 'T_a')
    sm = _State(length, loads, support_left, support_right, 'F_m', 'M_m', 'T_m')
    return sa, sm

def _strength_S(sa, sm, sections, Se, Syt, Kf, Kfs):
    best, info = -1.0, None
    for x, side in sections:
        Ma, Mm = sa.moment(x, side), sm.moment(x, side)
        Ta, Tm = sa.torque(x, side), sm.torque(x, side)
        S = math.sqrt(
            4.0 * ((Kf * Ma / Se) ** 2 + (Kf * Mm / Syt) ** 2) +
            3.0 * ((Kfs * Ta / Se) ** 2 + (Kfs * Tm / Syt) ** 2))
        if S > best:
            best = S
            info = {"x": x, "Ma": Ma, "Mm": Mm, "Ta": Ta, "Tm": Tm}
    return best, info

def _twist_sum(sa, sm, length, loads):
    xs = sorted(set([0.0, length] + [l['x'] for l in loads]))
    total = 0.0
    for x1, x2 in zip(xs[:-1], xs[1:]):
        mid = 0.5 * (x1 + x2)
        T_peak = sa.torque(mid, '+') + sm.torque(mid, '+')
        total += T_peak * (x2 - x1)
    return total

def compute_shaft_design(length, loads, support_left, support_right,
                         fos, d_max, theta_max, material_name,
                         ka, kb, kc, Kt, Kts, q, q_s):
    _validate(length, loads, fos, theta_max, d_max)

    mat = MATERIALS_DB[material_name]
    Sut, Syt, G = mat["Sut"], mat["Syt"], mat["G"]
    warnings = []
    if not mat.get("verified", True):
        warnings.append(f"{material_name}: not fully verified. {mat.get('src', '')}")

    sa, sm = solve_reactions_and_moments(length, loads, support_left, support_right)
    sections = _sections(length, loads)

    if support_left == "Fixed" and support_right == "Fixed":
        warnings.append("Fixed-Fixed is statically indeterminate; analysed as simply "
                        "supported.")
    if sa.mode == "propped":
        warnings.append("Fixed - Pin/Roller solved as a propped cantilever (constant EI).")
    if support_left != "Fixed" and support_right != "Fixed":
        if abs(sa.total_T) > 1e-6 or abs(sm.total_T) > 1e-6:
            warnings.append(
                "Torques do not sum to zero and neither end is fixed. Enter the output "
                "(driven) torque with the opposite sign so the shaft is in equilibrium.")

    auto_kb = kb is None

    def Se_Kf_Kfs(d):
        kb_val = size_factor(d) if auto_kb else kb
        Se, Kf, Kfs = calculate_fatigue_factors(mat, ka, kb_val, kc, Kt, Kts, q, q_s)
        return Se, Kf, Kfs, kb_val

    d = 30.0
    for _ in range(100):
        Se, Kf, Kfs, kb_used = Se_Kf_Kfs(d)
        S, crit = _strength_S(sa, sm, sections, Se, Syt, Kf, Kfs)
        d_new = ((16.0 * fos / math.pi) * S) ** (1.0 / 3.0)
        if abs(d_new - d) < 1e-7:
            d = d_new
            break
        d = d_new
    d_strength = d

    tw = _twist_sum(sa, sm, length, loads)
    d_rigidity = ((584.0 * tw) / (G * theta_max)) ** 0.25 if tw > 0 else 0.0

    d_required = max(d_strength, d_rigidity)
    governing = "Strength (fatigue)" if d_strength >= d_rigidity else "Torsional rigidity"

    selected_std_d, n_actual, actual_theta = None, None, None
    for d_std in STANDARD_DIAMETERS:
        if d_std < d_required - 1e-9:
            continue
        Se_s, Kf_s, Kfs_s, _ = Se_Kf_Kfs(d_std)
        S_s, _ = _strength_S(sa, sm, sections, Se_s, Syt, Kf_s, Kfs_s)
        n_s = math.pi * d_std ** 3 / (16.0 * S_s) if S_s > 0 else float("inf")
        th_s = 584.0 * tw / (G * d_std ** 4)
        if n_s >= fos - 1e-9 and th_s <= theta_max + 1e-9:
            selected_std_d, n_actual, actual_theta = d_std, n_s, th_s
            break

    reasons = []
    if selected_std_d is None:
        reasons.append(f"No standard diameter up to {STANDARD_DIAMETERS[-1]} mm is large enough.")
        actual_theta = 584.0 * tw / (G * d_required ** 4) if d_required > 0 else 0.0
    else:
        if selected_std_d > d_max:
            reasons.append(
                f"Required standard diameter {selected_std_d} mm exceeds the maximum "
                f"allowed {d_max:g} mm.")
    is_valid = selected_std_d is not None and selected_std_d <= d_max
    if selected_std_d is None and d_required > d_max:
        reasons.append(f"Calculated diameter {d_required:.2f} mm exceeds the maximum "
                       f"allowed {d_max:g} mm.")
    if is_valid is False and selected_std_d is not None and actual_theta > theta_max:
        reasons.append("Angle of twist exceeds the limit.")

    d_for_report = selected_std_d if selected_std_d else d_required
    Se_r, Kf_r, Kfs_r, kb_r = Se_Kf_Kfs(d_for_report)

    return {
        "success": is_valid,
        "reasons": reasons,
        "warnings": warnings,
        "governing": governing,
        "d_strength": d_strength,
        "d_rigidity": d_rigidity,
        "d_calculated": d_required,
        "d_standard": selected_std_d,
        "d_max": d_max,
        "n_actual": n_actual,
        "fos_required": fos,
        "kb_used": kb_r,
        "actual_theta": actual_theta,
        "theta_max": theta_max,
        "material": material_name,
        "Sut": Sut,
        "Syt": Syt,
        "R1_a": sa.R1, "R1_m": sm.R1,
        "R2_a": sa.R2, "R2_m": sm.R2,
        "T_R1_a": sa.T_R1, "T_R1_m": sm.T_R1,
        "T_R2_a": sa.T_R2, "T_R2_m": sm.T_R2,
        "critical_x": crit["x"],
        "M_a": crit["Ma"], "M_m": crit["Mm"],
        "T_a": crit["Ta"], "T_m": crit["Tm"],
        "Kf": Kf_r, "Kfs": Kfs_r, "Se": Se_r,
    }

def check_all_materials(length, loads, support_left, support_right,
                        fos, d_max, theta_max, ka, kb, kc, Kt, Kts, q, q_s):
    out = []
    for name in MATERIALS_DB:
        try:
            out.append((name, compute_shaft_design(
                length, loads, support_left, support_right, fos, d_max, theta_max,
                name, ka, kb, kc, Kt, Kts, q, q_s)))
        except ValueError as e:
            out.append((name, {"error": str(e)}))
    return out
