"""
math3d.py
---------
Matematică matriceală pentru un motor de modelare 3D.
Toate matricele sunt array-uri numpy 4×4 (float64) în coordonate omogene.
"""

import numpy as np


def translatie(tx: float, ty: float, tz: float) -> np.ndarray:
    """Returneaza o matrice de translatie."""
    matrice = np.eye(4, dtype=np.float64)
    matrice[0, 3] = tx
    matrice[1, 3] = ty
    matrice[2, 3] = tz
    return matrice


def scalare(sx: float, sy: float, sz: float) -> np.ndarray:
    """Returnează o matrice de scalare 4x4 uniformă/neuniformă."""
    return np.diag([sx, sy, sz, 1.0]).astype(np.float64)


def rotatie_x(unghi: float) -> np.ndarray:
    """Returnează o matrice de rotație 4x4 în jurul axei X (unghi în radiani)."""
    c, s = np.cos(unghi), np.sin(unghi)
    return np.array([
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1],
    ], dtype=np.float64)


def rotatie_y(unghi: float) -> np.ndarray:
    """Returnează o matrice de rotație 4x4 în jurul axei Y (unghi în radiani)."""
    c, s = np.cos(unghi), np.sin(unghi)
    return np.array([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1],
    ], dtype=np.float64)


def rotatie_z(unghi: float) -> np.ndarray:
    """Returnează o matrice de rotație 4x4 în jurul axei Z (unghi în radiani)."""
    c, s = np.cos(unghi), np.sin(unghi)
    return np.array([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# Proiecție în perspectivă (trunchi de vizualizare)
# ---------------------------------------------------------------------------

def matricea_volumului_de_vizualizare(
        stanga: float, dreapta: float,
        jos: float, sus: float,
        aproape: float, departe: float,
) -> np.ndarray:
    """
    Ce setează:
      • X  →  [stanga, dreapta] se limitează la [-1, 1]
      • Y  →  [jos, sus] se limitează la [-1, 1]
      • Z  →  [-aproape, -departe] la  [-1, 1]
      • -Z →  W

    Parametrii
    ----------
    stanga, dreapta : marginile orizontale ale planului apropiat
    jos, sus        : marginile verticale ale planului apropiat
    aproape, departe: distanțele pozitive către planurile apropiat și departe
    """
    rl = dreapta - stanga
    js = sus - jos
    da = departe - aproape

    return np.array([
        [2 * aproape / rl, 0, (dreapta + stanga) / rl, 0],
        [0, 2 * aproape / js, (sus + jos) / js, 0],
        [0, 0, -(departe + aproape) / da, -2 * departe * aproape / da],
        [0, 0, -1, 0],
    ], dtype=np.float64)


def proiectie_perspectiva(
        unghi_vizual: float, aspect: float,
        aproape: float, departe: float,
) -> np.ndarray:
    """
    unghi_vizual   : unghiul campului vizual
    aspect         : latimea ecranului impartita la inaltime
    aproape        : distanta pana la planul apropiat
    departe        : distanta pana la planul indepartat
    """
    sus = aproape * np.tan(unghi_vizual / 2.0)
    jos = -sus
    dreapta = sus * aspect
    stanga = -dreapta
    return matricea_volumului_de_vizualizare(stanga, dreapta, jos, sus, aproape, departe)


# ---------------------------------------------------------------------------
# Intersecție rază
# ---------------------------------------------------------------------------

def intersectie_raza_triunghi(
        origine: np.ndarray,
        directie: np.ndarray,
        v0: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        epsilon: float = 1e-8,
) -> float | None:
    """
    Intersecție rază-triunghi Möller–Trumbore.

    Returnează distanța *t* de-a lungul *directiei* până la punctul de impact,
    sau None dacă nu există intersecție (sau aceasta este în spatele razei).
    """
    muchie1 = v1 - v0
    muchie2 = v2 - v0
    h = np.cross(directie, muchie2)
    a = np.dot(muchie1, h)
    if abs(a) < epsilon:
        return None  # raza paralelă cu triunghiul
    f = 1.0 / a
    s = origine - v0
    u = f * np.dot(s, h)
    if u < 0.0 or u > 1.0:
        return None
    q = np.cross(s, muchie1)
    v = f * np.dot(directie, q)
    if v < 0.0 or u + v > 1.0:
        return None
    t = f * np.dot(muchie2, q)
    return float(t) if t > epsilon else None


def raza(
        origine: np.ndarray,
        directie: np.ndarray,
        varfuri: np.ndarray,
        fete: np.ndarray,
) -> tuple[float, int, np.ndarray] | None:
    """
    Găsește cea mai apropiată față lovită de rază.

    Returnează (t, indice_fata, punct_lovit) sau None dacă nu există lovitură.
    """
    cel_mai_bun_t = np.inf
    cea_mai_buna_fata = -1
    varfuri3 = varfuri[:, :3]  # elimină w

    for indice_fata, fata in enumerate(fete):
        i0, i1, i2 = int(fata[0]), int(fata[1]), int(fata[2])
        t = intersectie_raza_triunghi(
            origine, directie,
            varfuri3[i0], varfuri3[i1], varfuri3[i2],
        )
        if t is not None and t < cel_mai_bun_t:
            cel_mai_bun_t = t
            cea_mai_buna_fata = indice_fata

    if cea_mai_buna_fata < 0:
        return None
    punct_lovit = origine + directie * cel_mai_bun_t
    return cel_mai_bun_t, cea_mai_buna_fata, punct_lovit


def compune(*matrici: np.ndarray) -> np.ndarray:
    """
    Compune un număr arbitrar de matrice 4×4 (aplicare de la stânga la dreapta).
    compune(A, B, C)  →  C @ B @ A   (A se aplică primul).
    """
    rezultat = np.eye(4, dtype=np.float64)
    for matrice in matrici:
        rezultat = matrice @ rezultat
    return rezultat
