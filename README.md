# Motor de Modelare 3D

Un motor de modelare 3D scris în Python, fără GPU — doar `numpy` și `pygame`.
Suportă editare de vârfuri, creare de fețe, import/export `.obj` și mai multe moduri de randare.

---

## Cerințe

```bash
pip install -r requirements.txt
```

> Python 3.10+ recomandat.

---

## Pornire

```bash
python main.py
```

La pornire apare un meniu de selecție a plasei de start:

| Plasă | Vârfuri | Fețe |
|-------|---------|------|
| Cub | 8 | 12 |
| Sferă | ~200 | ~380 |
| Tor | ~288 | ~576 |

Navighează cu ←/→ sau mouse, confirma cu Enter sau Click.

---

## Moduri de intrare

Programul are două moduri de control, comutate cu Space:

| Mod | Ce controlează |
|-----|---------------|
| `OBIECT` | Rotația și poziția obiectului 3D |
| `CAMERĂ` | Poziția și orientarea camerei în scenă |

---

## Taste generale

| Tastă | Acțiune |
|-------|---------|
| `Spațiu` | Comută între mod Obiect / Cameră |
| `↑ ↓ ← →` | Rotire (pitch / yaw) |
| `W / S` | Mișcare sus / jos |
| `A / D` | Mișcare stânga / dreapta |
| `Shift + W / S` | Mișcare înainte / înapoi |
| `O` | Ciclu mod randare: WIREFRAME → X-RAY → SOLID |
| `H` | Comută afișarea vârfurilor: TOATE / HOVER |
| `T` | Afișează / ascunde liniile de triunghi |
| `U` | Afișează / ascunde HUD-ul (ajutor pe ecran) |
| `R` | Resetează rotația și poziția la valorile inițiale |
| `ESC` | Înapoi la meniu |

---

## Moduri de randare (`O`)

| Mod | Descriere |
|-----|-----------|
| `WIREFRAME` | Doar muchiile obiectului |
| `X-RAY` | Fețe semi-transparente, se văd și cele din spate |
| `SOLID` | Randare solidă cu iluminare difuză |

---

## Editare vârfuri (`E`)

Apasă `E` pentru a intra în modul de editare. Fețele devin portocalii ca indicator vizual.

### Selectare

| Acțiune | Efect |
|---------|-------|
| Click pe un vârf | Selectează acel vârf (deselectează restul) |
| Ctrl + Click | Adaugă / elimină vârful din selecție multiplă |

### Mutare vârfuri

| Acțiune | Efect |
|---------|-------|
| Click și drag pe un vârf | Mută vârful (sau toate vârfurile selectate) |
| Vârf adăugat pe o față | Se mișcă constrâns pe planul feței respective |
| Vârf adăugat în spațiu liber | Se mișcă liber în planul ecranului |

### Adăugare vârfuri

| Tastă / Acțiune | Efect |
|-----------------|-------|
| `V` | Comută modul de plasare: SUPRAFAȚĂ / LIBER |
| Click pe o față (mod SUPRAFAȚĂ) | Adaugă un vârf exact pe suprafața feței (Möller–Trumbore) |
| Click pe fundal (mod LIBER) | Adaugă un vârf în spațiu 3D la adâncimea medie a meshului |

### Creare fețe

1. Click pe 3 vârfuri pe rând → apar evidențiate în verde
2. Apasă `F` → se creează o față triunghiulară nouă
3. Apasă `C` → șterge selecția curentă fără a crea fața
 
Fețele se creează manual — adăugarea unui vârf pe o față existentă nu o modifică automat.

---

## Salvare / Încărcare (`.obj`)

| Tastă | Acțiune |
|-------|---------|
| `Ctrl + S` | Salvează mesh-ul în format Wavefront `.obj` |
| `Ctrl + L` | Încarcă un fișier `.obj` de pe disc |

Se deschide un dialog grafic de fișiere. Rezultatul salvării/încărcării apare ca banner în partea de jos a ecranului.

---

## Structura proiectului

```
ModellingEngine/
├── main.py        # Bucla principală, input, HUD, randare
├── mesh.py        # Clasa Obiect (vârfuri, fețe, muchii)
├── math3d.py      # Matrice 3D, proiecție, raza Möller–Trumbore
├── objects.py     # Generatoare de plasă: cub, sferă, tor
├── io_obj.py      # Import / export Wavefront .obj
└── requirements.txt
```

---

## Dependințe

```
numpy - pip install numpy
pygame - pip install pygame sau pip install pygame-ce
```

---

---

