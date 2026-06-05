"""
mesh.py
-------
Definește clasa Obiect, care reprezintă un obiect 3D format din triunghiuri.

CUM ESTE STOCAT UN OBIECT 3D
-----------------------------
Un mesh este alcătuit din două componente:
  1. Vârfuri  – puncte în spațiul 3D, ex. cele 8 colțuri ale unui cub.
  2. Fețe     – triunghiuri care conectează acele puncte, ex. [0, 1, 2]
                înseamnă „desenează un triunghi folosind vârful 0, 1 și 2".

COORDONATE OMOGENE
------------------
Fiecare vârf este stocat nu ca [x, y, z] ci ca [x, y, z, 1].
Acel „1" de la sfârșit se numește coordonata omogenă.
Ne permite să aplicăm translație, rotație și scalare printr-o singură
înmulțire de matrice 4x4 — ceea ce este foarte eficient cu NumPy.

STRUCTURA DE STOCARE
--------------------
Toate cele N vârfuri sunt stocate într-un singur array NumPy de forma (N, 4):

    rândul 0   →  [x0, y0, z0, 1]   ← vârful 0
    rândul 1   →  [x1, y1, z1, 1]   ← vârful 1
    ...
    rândul N-1 →  [xN, yN, zN, 1]   ← ultimul vârf

Asta înseamnă că putem transforma toate vârfurile deodată printr-o singură
înmulțire de matrice, în loc să iterăm fiecare vârf individual.
"""

from __future__ import annotations
import numpy as np


class Obiect:
    """Reprezinta un obiect 3D format din varfuri, fete si optional muchii."""

    def __init__(self, varfuri, fete, muchii=None):
        v = np.asarray(varfuri, dtype=np.float64)
        if v.shape[1] == 3:
            coloana_unu = np.ones((v.shape[0], 1), dtype=np.float64)
            v = np.hstack([v, coloana_unu])  #
        self.varfuri = v
        self._varfuri_originale = v.copy()
        self.fete = np.asarray(fete, dtype=np.int32)
        if muchii is not None:
            self.muchii = np.asarray(muchii, dtype=np.int32)
        else:
            self.muchii = None

        self.transformare = np.eye(4, dtype=np.float64)

    # TRANSFORMĂRI LA NIVEL DE OBIECT
    # Acestea schimbă unde se află obiectul / cum este orientat în lume
    # prin actualizarea self.transformare. Datele vârfurilor nu sunt modificate.

    def seteaza_transformare(self, matrice4x4):
        """Înlocuiește transformarea obiectului cu o nouă matrice 4x4."""
        self.transformare = np.asarray(matrice4x4, dtype=np.float64)

    def aplica_transformare(self, matrice4x4):
        """
        Combină o nouă matrice 4x4 peste transformarea curentă.

            transformare_noua = matrice4x4  @  transformare_veche
        Deci noua matrice este aplicată după tot ce a venit înainte.
        """
        self.transformare = np.asarray(matrice4x4, dtype=np.float64) @ self.transformare

    def obtine_varfuri_lume(self):
        """
        Returnează pozițiile tuturor vârfurilor după aplicarea self.transformare.

        Returnează
        ----------
        np.ndarray de forma (N, 4) — vârfuri în spațiul lumii.
        """
        return (self.transformare @ self.varfuri.T).T

    # EDITĂRI LA NIVEL DE VÂRF
    # Acestea modifică direct poziția vârfurilor individuale în spațiul local.

    def muta_varf(self, index, dx, dy, dz):
        """
        Mută un vârf cu (dx, dy, dz) în spațiul local al meshului.

        Parametri
        ---------
        index : int   – vârful de mutat (numărul rândului în self.varfuri)
        dx, dy, dz    – cât de mult să se miște pe fiecare axă
        """
        self.varfuri[index, 0] += dx  # mișcare pe X
        self.varfuri[index, 1] += dy  # mișcare pe Y
        self.varfuri[index, 2] += dz  # mișcare pe Z

    def adauga_varf(self, x, y, z):
        """
        Adaugă un vârf nou la poziția (x, y, z).

        Returnează indexul vârfului nou, astfel încât apelanții să îl poată referenția.
        """
        rand_nou = np.array([[x, y, z, 1.0]], dtype=np.float64)  # forma (1, 4)

        # Adaugă noul rând la sfârșitul ambelor array-uri de vârfuri.
        self.varfuri = np.vstack([self.varfuri, rand_nou])
        self._varfuri_originale = np.vstack([self._varfuri_originale, rand_nou])

        return len(self.varfuri) - 1  # indexul vârfului nou adăugat

    def adauga_muchie(self, index_a, index_b):
        """
        Înregistrează o muchie între vârful index_a și vârful index_b.

        Verifică dublurile mai întâi (muchia A→B și B→A sunt aceeași muchie).
        """
        if self.muchii is None:
            # Nicio muchie încă — creează array-ul cu această singură muchie.
            self.muchii = np.array([[index_a, index_b]], dtype=np.int32)
            return

        # Verifică dacă muchia există deja în oricare direcție.
        exista_deja = bool(np.any(
            ((self.muchii[:, 0] == index_a) & (self.muchii[:, 1] == index_b)) |
            ((self.muchii[:, 0] == index_b) & (self.muchii[:, 1] == index_a))
        ))

        if not exista_deja:
            muchie_noua = np.array([[index_a, index_b]], dtype=np.int32)
            self.muchii = np.vstack([self.muchii, muchie_noua])

    def adauga_fata(self, index_a, index_b, index_c):
        """
        Adaugă o față triunghiulară formată din trei vârfuri existente.

        Înregistrează și cele trei muchii ale triunghiului, astfel încât
        desenul wireframe rămâne mereu actualizat.
        """
        triunghi_nou = np.array([[index_a, index_b, index_c]], dtype=np.int32)
        self.fete = np.vstack([self.fete, triunghi_nou])

        # Asigură că fiecare muchie a triunghiului este în self.muchii.
        self.adauga_muchie(index_a, index_b)
        self.adauga_muchie(index_b, index_c)
        self.adauga_muchie(index_c, index_a)

    def reseteaza_varfuri(self):
        """Readuce toate vârfurile la pozițiile din momentul creării meshului."""
        self.varfuri = self._varfuri_originale.copy()

    def __repr__(self):
        """Descriere scurtă afișată la print() al unui obiect Mesh."""
        return f"Obiect(varfuri={self.varfuri.shape}, fete={self.fete.shape})"
