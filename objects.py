"""
objects.py
----------
Funcții care returnează obiecte pre-construite.
"""

import numpy as np
from mesh import Obiect


def creeaza_cub(dimensiune: float = 1.0) -> Obiect:
    """
    Creeaza un cub.

    Schita cubului:

          6----7
         /|   /|
        2----3 |
        | 4--|-5
        |/   |/
        0----1
    """
    s = dimensiune / 2.0
    varfuri = np.array([
        [-s, -s, -s],  # 0
        [ s, -s, -s],  # 1
        [-s,  s, -s],  # 2
        [ s,  s, -s],  # 3
        [-s, -s,  s],  # 4
        [ s, -s,  s],  # 5
        [-s,  s,  s],  # 6
        [ s,  s,  s],  # 7
    ], dtype=np.float64)

    # 6 fețe * 2 triunghiuri = 12 triunghiuri
    fete = np.array([
        # față față
        [0, 3, 1],
        [0, 2, 3],
        # față spate
        [5, 6, 4],
        [5, 7, 6],
        # față stânga
        [4, 2, 0],
        [4, 6, 2],
        # față dreapta
        [1, 7, 5],
        [1, 3, 7],
        # față jos
        [4, 1, 5],
        [4, 0, 1],
        # față sus
        [2, 7, 3],
        [2, 6, 7],
    ], dtype=np.int32)

    muchii = np.array([
        # muchiile de jos
        [0, 1], [1, 5], [5, 4], [4, 0],
        # muchiile de sus
        [2, 3], [3, 7], [7, 6], [6, 2],
        # muchiile verticale
        [0, 2], [1, 3], [4, 6], [5, 7],
    ], dtype=np.int32)

    return Obiect(varfuri, fete, muchii)


def creeaza_sfera(raza: float = 1.0, straturi: int = 12, felii: int = 16) -> Obiect:
    """
    Sferă UV centrată în origine.
    straturi = numărul de inele orizontale (diviziuni de latitudine)
    felii    = numărul de segmente verticale (diviziuni de longitudine)
    """
    varfuri = []
    # Pol de sus
    varfuri.append([0.0, raza, 0.0])

    for i in range(1, straturi):
        phi = np.pi * i / straturi          # 0 (sus) → pi (jos)
        y   = raza * np.cos(phi)
        r   = raza * np.sin(phi)
        for j in range(felii):
            theta = 2.0 * np.pi * j / felii
            varfuri.append([r * np.sin(theta), y, r * np.cos(theta)])

    # Pol de jos
    varfuri.append([0.0, -raza, 0.0])

    varfuri = np.array(varfuri, dtype=np.float64)
    fete    = []
    set_muchii: set[tuple[int, int]] = set()

    def adauga_muchie(a, b):
        cheie = (min(a, b), max(a, b))
        set_muchii.add(cheie)

    varf_sus = 0
    varf_jos = len(varfuri) - 1

    def indice_inel(indice_strat, indice_felie):
        # strat_i: 0 … straturi-2  →  rânduri de vârfuri inel
        return 1 + indice_strat * felii + (indice_felie % felii)

    # Capacul de sus
    for j in range(felii):
        a = indice_inel(0, j)
        b = indice_inel(0, j + 1)
        fete.append([varf_sus, a, b])
        adauga_muchie(varf_sus, a)
        adauga_muchie(a, b)

    #  mijloc (fiecare împărțit în 2 triunghiuri)
    for i in range(straturi - 2):
        for j in range(felii):
            a = indice_inel(i, j)
            b = indice_inel(i, j + 1)
            c = indice_inel(i + 1, j + 1)
            d = indice_inel(i + 1, j)
            fete.append([a, b, c])
            fete.append([a, c, d])
            adauga_muchie(a, b)
            adauga_muchie(b, c)
            adauga_muchie(c, d)
            adauga_muchie(d, a)

    # Capac de jos
    for j in range(felii):
        a = indice_inel(straturi - 2, j)
        b = indice_inel(straturi - 2, j + 1)
        fete.append([b, a, varf_jos])
        adauga_muchie(a, varf_jos)
        adauga_muchie(b, varf_jos)

    fete = np.array(fete, dtype=np.int32)
    muchii = np.array(list(set_muchii), dtype=np.int32)
    return Obiect(varfuri, fete, muchii)


def creeaza_tor(raza_mare: float = 1.0, raza_mica: float = 0.4,
                segmente_mari: int = 24, segmente_mici: int = 12) -> Obiect:
    """
    Tor centrat în origine, care se rotește în jurul axei Y.
    raza_mare = distanța de la centrul torului la centrul tubului
    raza_mica = raza tubului
    """
    varfuri = []
    for i in range(segmente_mari):
        phi = 2.0 * np.pi * i / segmente_mari
        for j in range(segmente_mici):
            theta = 2.0 * np.pi * j / segmente_mici
            x = (raza_mare + raza_mica * np.cos(theta)) * np.cos(phi)
            y = raza_mica * np.sin(theta)
            z = (raza_mare + raza_mica * np.cos(theta)) * np.sin(phi)
            varfuri.append([x, y, z])

    varfuri = np.array(varfuri, dtype=np.float64)
    fete    = []
    set_muchii: set[tuple[int, int]] = set()

    def indice(i, j):
        return (i % segmente_mari) * segmente_mici + (j % segmente_mici)

    def adauga_muchie(a, b):
        set_muchii.add((min(a, b), max(a, b)))

    for i in range(segmente_mari):
        for j in range(segmente_mici):
            a = indice(i, j)
            b = indice(i, j + 1)
            c = indice(i + 1, j + 1)
            d = indice(i + 1, j)
            fete.append([a, b, c])
            fete.append([a, c, d])
            adauga_muchie(a, b)
            adauga_muchie(b, c)
            adauga_muchie(c, d)
            adauga_muchie(d, a)

    fete = np.array(fete, dtype=np.int32)
    muchii = np.array(list(set_muchii), dtype=np.int32)
    return Obiect(varfuri, fete, muchii)
