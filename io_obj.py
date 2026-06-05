"""
io_obj.py
---------
Import / export fișiere Wavefront .obj.

- incarca_obj  : citește un fișier .obj (din Blender, Maya etc.) → Mesh
- salveaza_obj : scrie Mesh-ul curent într-un fișier .obj
"""

from __future__ import annotations
import numpy as np
from pathlib import Path
from mesh import Obiect


def incarca_obj(cale: str | Path) -> Obiect:
    """
    Parsează un fișier Wavefront .obj și returnează un Mesh.

    Suportă:
      • v   – poziții vârfuri
      • f   – definiții fețe (triunghiuri, quads, triangulate automat)
            indicii fețelor pot fi  v,  v/vt,  v/vt/vn,  sau  v//vn
    Ignoră: vt, vn, mtl, grupuri, obiecte, grupuri de netezire.
    """
    cale = Path(cale)
    varfuri_brute: list[list[float]] = []
    fete_brute: list[list[int]] = []

    with open(cale, "r", encoding="utf-8", errors="replace") as fisier:
        for rand_brut in fisier:
            linie = rand_brut.strip()
            if not linie or linie.startswith("#"):
                continue

            parti = linie.split()
            simbol = parti[0]

            if simbol == "v":
                varfuri_brute.append([float(parti[1]), float(parti[2]), float(parti[3])])

            elif simbol == "f":
                indici = [int(p.split("/")[0]) - 1 for p in parti[1:]]
                # Triangulare fan pentru quads / n-goane
                for k in range(1, len(indici) - 1):
                    fete_brute.append([indici[0], indici[k], indici[k + 1]])

    if not varfuri_brute:
        raise ValueError(f"Niciun vârf găsit în {cale}")

    varfuri = np.array(varfuri_brute, dtype=np.float64)
    fete = np.array(fete_brute, dtype=np.int32)

    # Construiește setul de muchii din fețe
    set_muchii: set[tuple[int, int]] = set()
    for fata in fete_brute:
        for a, b in ((fata[0], fata[1]), (fata[1], fata[2]), (fata[2], fata[0])):
            set_muchii.add((min(a, b), max(a, b)))
    muchii = np.array(list(set_muchii), dtype=np.int32) if set_muchii else None

    return Obiect(varfuri, fete, muchii)


def salveaza_obj(plasa: Obiect, cale: str | Path, nume: str = "mesh") -> None:
    """
    Scrie un Mesh într-un fișier Wavefront .obj.

    Folosește pozițiile *locale* ale vârfurilor (înainte de orice transformare).
    """
    cale = Path(cale)
    linii: list[str] = []
    linii.append("# Exportat de Motorul de Modelare 3D")
    linii.append(f"o {nume}")
    linii.append("")

    # Vârfuri (spațiu local, fără w)
    for varf in plasa.varfuri:
        linii.append(f"v {varf[0]:.6f} {varf[1]:.6f} {varf[2]:.6f}")
    linii.append("")

    # Fețe (indici cu baza 1)
    for fata in plasa.fete:
        linii.append(f"f {fata[0]+1} {fata[1]+1} {fata[2]+1}")

    cale.write_text("\n".join(linii) + "\n", encoding="utf-8")
