import sys
import numpy as np
import pygame

from math3d import (
    rotatie_x, rotatie_y, rotatie_z,
    translatie, proiectie_perspectiva, compune,
    raza,
)
from mesh import Obiect
from objects import creeaza_cub, creeaza_sfera, creeaza_tor
from io_obj import incarca_obj, salveaza_obj

# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS   = 60
FOV_Y = np.radians(60.0)
ASPECT = WIDTH / HEIGHT
NEAR, FAR = 0.1, 100.0

BG_COLOR        = (15,  15,  25)
FACE_COLOR      = (60,  120, 200)
FACE_COLOR_EDIT = (200, 90,  60)
WIRE_COLOR      = (220, 230, 255)
EDIT_WIRE       = (255, 200, 80)
HIGHLIGHT       = (255, 80,  80)
SEL_COLOR       = (80,  220, 120)
TEXT_COLOR      = (200, 220, 255)
TRIANGLE_COLOR  = (255, 255, 120)

CLICK_THRESH_PX = 5
PICK_RADIUS_PX  = 20

# ---------------------------------------------------------------------------

def ndc_la_ecran(ndc_x, ndc_y):
    ecran_x = (ndc_x + 1.0) * 0.5 * WIDTH
    ecran_y = (1.0 - ndc_y) * 0.5 * HEIGHT
    return np.stack([ecran_x, ecran_y], axis=-1)


def deproiecteaza_ecran(mx, my, tinta_vizualizare_z, matrice_proiectie, inv_obiect):
    ndc_x = (mx / WIDTH) * 2.0 - 1.0
    ndc_y = -(my / HEIGHT) * 2.0 + 1.0
    clip_w = -tinta_vizualizare_z
    viz_x = ndc_x * clip_w / matrice_proiectie[0, 0]
    viz_y = ndc_y * clip_w / matrice_proiectie[1, 1]
    local = inv_obiect @ np.array([viz_x, viz_y, tinta_vizualizare_z, 1.0])
    return local[:3]


def construieste_vizualizare(cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw):
    return compune(
        translatie(-cam_tx, -cam_ty, -cam_tz),
        rotatie_y(-cam_yaw),
        rotatie_x(-cam_pitch),
    )


def deseneaza_hud(
    ecran,
    font,
    suprafata_hud,
    camera_mode,
    cam_tx,
    cam_ty,
    cam_tz,
    cam_pitch,
    cam_yaw,
    pitch,
    yaw,
    tx,
    ty,
    tz,
    editare_varfuri,
    varfuri_selectate,
    plasare_libera,
    fete_selectate,
    numar_varfuri,
    obiect,
    mod_randare,
    doar_varfuri_hover,
    afisare_triunghiuri,
    afisare_ajutor,
    mesaj_stare,
    timer_stare,
):
    if not afisare_ajutor:
        return

    mode_str  = "CAMERĂ" if camera_mode else "OBIECT"
    edit_str  = "ACTIV" if editare_varfuri else "INACTIV"
    face_hint = ""
    place_str = ""
    sel_str   = ""
    if editare_varfuri:
        sel_str   = f"  [{len(varfuri_selectate)} selectate]" if varfuri_selectate else ""
        place_str = f"   Plasare: {'LIBER' if plasare_libera else 'SUPRAFAȚĂ'}  (V)"
        if len(fete_selectate) == 3:
            face_hint = "  → F=crează față  C=șterge sel."
        elif len(fete_selectate) > 0:
            face_hint = f"  ({len(fete_selectate)}/3 selectate)"

    linie_camera = (f"Poz. cameră: ({cam_tx:.2f}, {cam_ty:.2f}, {cam_tz:.2f})  "
                f"Pitch: {np.degrees(cam_pitch):.1f}°  Yaw: {np.degrees(cam_yaw):.1f}°"
                if camera_mode else
                f"Pitch: {np.degrees(pitch):.1f}°  Yaw: {np.degrees(yaw):.1f}°  "
                f"Poz: ({tx:.2f}, {ty:.2f}, {tz:.2f})")

    triunghiuri_str = "ACTIV" if afisare_triunghiuri else "INACTIV"
    ajutor_str = "ACTIV" if afisare_ajutor else "INACTIV"
    linii_hud = [
        "Motor de modelare 3D (numpy + pygame)",
        f"Mod intrare: {mode_str}  (Spațiu pt. comutare)    Editare vârfuri: {edit_str}{face_hint}{place_str}{sel_str if editare_varfuri else ''}",
        f"Vârfuri: {numar_varfuri}   Fețe: {len(obiect.fete)}",
        linie_camera,
        f"Randare: {['WIREFRAME','X-RAY','SOLID'][mod_randare]}  (O)   "
        f"Vârfuri: {'HOVER' if doar_varfuri_hover else 'TOATE'}  (H)   Triunghiuri: {triunghiuri_str}  (T)   Ajutor: {ajutor_str}  (U)",
    ]
    linii_hud.extend([
        "Săgeți=rotire  WASD=mișcare  Shift+W/S=înainte/înapoi  Space=cam/obj  E=editare  O=randare  H=hover  T=triunghiuri  U=ajutor  R=reset  ESC=meniu",
        "Ctrl+click=multisel  V=liber/suprafață  F=față  C=șterge sel.  Ctrl+S=salvare  Ctrl+L=încărcare",
    ])
    y_off = 8
    for line in linii_hud:
        if line:
            ecran.blit(suprafata_hud(line), (8, y_off))
        y_off += 16

    # banner mesaje
    if timer_stare > 0 and mesaj_stare:
        alpha  = min(1.0, timer_stare)
        s_surf = font.render(mesaj_stare, True, (20, 20, 30))
        pad    = 8
        bw, bh = s_surf.get_width() + pad*2, s_surf.get_height() + pad*2
        banner = pygame.Surface((bw, bh), pygame.SRCALPHA)
        banner.fill((180, 230, 120, int(alpha * 220)))
        banner.blit(s_surf, (pad, pad))
        ecran.blit(banner, (WIDTH//2 - bw//2, HEIGHT - 60))


def ruleaza_meniu(ecran: pygame.Surface, ceas: pygame.time.Clock) -> Obiect:
    font_titlu = pygame.font.SysFont("consolas", 36, bold=True)
    font_sub = pygame.font.SysFont("consolas", 18)
    font_hint = pygame.font.SysFont("consolas", 13)

    optiuni = [
        ("Cub", lambda: creeaza_cub(dimensiune=1.5), "8 vârfuri · 12 fețe"),
        ("Sferă", lambda: creeaza_sfera(raza=1.0), "~200 vârfuri · ~380 fețe"),
        ("Tor", lambda: creeaza_tor(), "~288 vârfuri · ~576 fețe"),
    ]

    # constante layout
    CARD_W, CARD_H = 220, 110
    GAP = 30
    latime_totala = len(optiuni) * CARD_W + (len(optiuni) - 1) * GAP
    start_x = (WIDTH - latime_totala) // 2
    card_y = HEIGHT // 2 - CARD_H // 2
    carduri = [pygame.Rect(start_x + i * (CARD_W + GAP), card_y, CARD_W, CARD_H)
               for i in range(len(optiuni))]
    selectat = 0

    while True:
        ceas.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selectat = (selectat - 1) % len(optiuni)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selectat = (selectat + 1) % len(optiuni)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return optiuni[selectat][1]()
            elif event.type == pygame.MOUSEMOTION:
                ex, ey = event.pos
                for i, r in enumerate(carduri):
                    if r.collidepoint(ex, ey):
                        selectat = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ex, ey = event.pos
                for i, r in enumerate(carduri):
                    if r.collidepoint(ex, ey):
                        return optiuni[i][1]()

        ecran.fill(BG_COLOR)

        title = font_titlu.render("Motor de modelare 3D", True, TEXT_COLOR)
        ecran.blit(title, title.get_rect(centerx=WIDTH // 2, y=HEIGHT // 4 - 40))
        sub = font_sub.render("Alege un obiect de pornire", True, (140, 160, 200))
        ecran.blit(sub, sub.get_rect(centerx=WIDTH // 2, y=HEIGHT // 4 + 14))

        for i, (label, _, hint) in enumerate(optiuni):
            rect    = carduri[i]
            hovered = (i == selectat)
            bg      = (40, 60, 100) if not hovered else (70, 110, 190)
            border  = (100, 140, 220) if not hovered else (180, 220, 255)
            pygame.draw.rect(ecran, bg,     rect, border_radius=10)
            pygame.draw.rect(ecran, border, rect, width=2, border_radius=10)

            lbl = font_sub.render(label, True, (255, 255, 255))
            ecran.blit(lbl, lbl.get_rect(centerx=rect.centerx, y=rect.y + 20))

            ht = font_hint.render(hint, True, (160, 180, 210))
            ecran.blit(ht, ht.get_rect(centerx=rect.centerx, y=rect.y + 55))

            if hovered:
                ind = font_hint.render("▶ Apasă Enter / Click ◀", True, (220, 240, 120))
                ecran.blit(ind, ind.get_rect(centerx=rect.centerx, y=rect.y + 82))

        pygame.display.flip()


# ---------------------------------------------------------------------------

def main(ecran: pygame.Surface, ceas: pygame.time.Clock) -> None:
    font  = pygame.font.SysFont("consolas", 14)

    # ---- Ecran de pornire: alege un obiect ----
    obiect     = ruleaza_meniu(ecran, ceas)
    matrice_proiectie = proiectie_perspectiva(FOV_Y, ASPECT, NEAR, FAR)

    # --- Starea obiectului (model) ---
    pitch = yaw = roll = 0.0
    tx = ty = tz = 0.0

    # --- Starea camerei (vizualizare) ---
    cam_tx, cam_ty, cam_tz   = 0.0, 0.0, 4.0
    cam_pitch, cam_yaw        = 0.0, 0.0
    camera_mode               = False   # Spațiu comută

    # Stare interacțiune
    mod_randare     = 2       # 0=wireframe  1=x-ray  2=solid
    afisare_triunghiuri = False
    afisare_ajutor      = True
    doar_varfuri_hover = False
    editare_varfuri     = False
    varf_tras     = -1
    pick_in_asteptare    = -1
    pozitie_mouse_apasat  = (0, 0)
    are_pozitie_mouse_apasat = False

    fete_selectate: list[int] = []
    plasare_libera = False
    plan_varf: dict[int, tuple[np.ndarray, float]] = {}
    varfuri_selectate:  set[int] = set()   # selecție multiplă
    # Pentru drag în grup: offsetul în spațiu local al fiecărui vârf selectat față de
    # vârful tras în momentul în care începe drag-ul
    decalaje_tras: dict[int, np.ndarray] = {}

    mesaj_stare      = ""       # afișat în HUD câteva secunde
    timer_stare    = 0.0      # secunde rămase

    dt = 1.0 / FPS

    numar_varfuri       = len(obiect.varfuri)
    puncte_ecran    = np.zeros((numar_varfuri, 2), dtype=np.float64)
    puncte_ecran_i  = np.zeros((numar_varfuri, 2), dtype=np.int32)
    varfuri_clip    = np.zeros((numar_varfuri, 4), dtype=np.float64)
    varfuri_lume   = np.zeros((numar_varfuri, 4), dtype=np.float64)
    transformare_obiect = np.eye(4, dtype=np.float64)
    inv_obiect       = np.eye(4, dtype=np.float64)
    indici_fete_sortate     = np.empty(0, dtype=np.int64)
    medie_z_sortata   = np.empty(0, dtype=np.float64)
    nuante_fete   = np.empty(0, dtype=np.float64)
    nuante_xray   = np.empty(0, dtype=np.float64)
    indici_fete_xray       = np.empty(0, dtype=np.int64)

    recalculeaza_transformari = True

    _hud_cache: dict[str, pygame.Surface] = {}
    def suprafata_hud(text: str) -> pygame.Surface:
        if text not in _hud_cache:
            _hud_cache[text] = font.render(text, True, TEXT_COLOR)
        return _hud_cache[text]

    def proceseaza_keydown(event: pygame.event.Event) -> None:
        nonlocal running, mod_randare, doar_varfuri_hover, afisare_triunghiuri
        nonlocal afisare_ajutor
        nonlocal camera_mode, cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw
        nonlocal pitch, yaw, roll, tx, ty, tz, recalculeaza_transformari
        nonlocal editare_varfuri, varf_tras, pick_in_asteptare, fete_selectate
        nonlocal plasare_libera, obiect, numar_varfuri, varfuri_selectate
        nonlocal plan_varf, decalaje_tras, mesaj_stare, timer_stare

        if event.key == pygame.K_ESCAPE:
            running = False   # înapoi la meniu
        elif event.key == pygame.K_o:
            mod_randare = (mod_randare + 1) % 3
        elif event.key == pygame.K_h:
            doar_varfuri_hover = not doar_varfuri_hover
        elif event.key == pygame.K_t:
            afisare_triunghiuri = not afisare_triunghiuri
        elif event.key == pygame.K_u:
            afisare_ajutor = not afisare_ajutor
        elif event.key == pygame.K_SPACE:
            camera_mode = not camera_mode
        elif event.key == pygame.K_r:
            if camera_mode:
                cam_tx = cam_ty = cam_pitch = cam_yaw = 0.0
                cam_tz = 4.0
            else:
                pitch = yaw = roll = tx = ty = tz = 0.0
            recalculeaza_transformari = True
        elif event.key == pygame.K_e:
            editare_varfuri = not editare_varfuri
            varf_tras = pick_in_asteptare = -1
            fete_selectate.clear()
        elif event.key == pygame.K_v and editare_varfuri:
            plasare_libera = not plasare_libera
        elif event.key == pygame.K_f and editare_varfuri and len(fete_selectate) == 3:
            obiect.adauga_fata(fete_selectate[0], fete_selectate[1], fete_selectate[2])
            fete_selectate.clear()
            numar_varfuri = len(obiect.varfuri)
            recalculeaza_transformari = True
        elif event.key == pygame.K_c and editare_varfuri:
            fete_selectate.clear()

        # ---- Fișiere I/O ----
        elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
                p = filedialog.asksaveasfilename(
                    title="Save mesh",
                    defaultextension=".obj",
                    filetypes=[("Wavefront OBJ", "*.obj"), ("All files", "*.*")])
                root.destroy()
                if p:
                    salveaza_obj(obiect, p)
                    mesaj_stare   = f"Salvat → {p}"
                    timer_stare = 3.0
            except Exception as exc:
                mesaj_stare   = f"Salvare eșuată: {exc}"
                timer_stare = 4.0

        elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
                p = filedialog.askopenfilename(
                    title="Load mesh",
                    filetypes=[("Wavefront OBJ", "*.obj"), ("All files", "*.*")])
                root.destroy()
                if p:
                    obiect         = incarca_obj(p)
                    numar_varfuri      = len(obiect.varfuri)
                    varfuri_selectate    = set()
                    fete_selectate     = []
                    plan_varf = {}
                    decalaje_tras = {}
                    varf_tras  = pick_in_asteptare = -1
                    recalculeaza_transformari = True
                    mesaj_stare   = f"Încărcat ← {p}  ({numar_varfuri} vârfuri, {len(obiect.fete)} fețe)"
                    timer_stare = 3.0
            except Exception as exc:
                mesaj_stare   = f"Încărcare eșuată: {exc}"
                timer_stare = 4.0

    def proceseaza_mouse_down_edit(event: pygame.event.Event) -> None:
        nonlocal pozitie_mouse_apasat, are_pozitie_mouse_apasat, pick_in_asteptare, varfuri_selectate, varf_tras

        mx, my = event.pos
        pozitie_mouse_apasat = (mx, my)
        are_pozitie_mouse_apasat = True
        dists   = np.hypot(puncte_ecran[:, 0] - mx, puncte_ecran[:, 1] - my)
        best_vi = int(np.argmin(dists))
        ctrl    = pygame.key.get_mods() & pygame.KMOD_CTRL

        if dists[best_vi] < PICK_RADIUS_PX:
            pick_in_asteptare = best_vi
            if ctrl:
                if best_vi in varfuri_selectate:
                    varfuri_selectate.discard(best_vi)
                else:
                    varfuri_selectate.add(best_vi)
            else:
                if best_vi not in varfuri_selectate:
                    varfuri_selectate = {best_vi}
        else:
            pick_in_asteptare = -1
            if not ctrl:
                varfuri_selectate.clear()
        varf_tras  = -1

    def proceseaza_mouse_motion_edit(event: pygame.event.Event) -> None:
        nonlocal varf_tras, varfuri_selectate, decalaje_tras, recalculeaza_transformari
        nonlocal are_pozitie_mouse_apasat

        mouse_down_pos = pozitie_mouse_apasat
        if pick_in_asteptare >= 0 and are_pozitie_mouse_apasat:
            mdx = float(mouse_down_pos[0])
            mdy = float(mouse_down_pos[1])
            moved = np.hypot(event.pos[0] - mdx,
                             event.pos[1] - mdy)
            if moved > CLICK_THRESH_PX:
                varf_tras = pick_in_asteptare
                if varf_tras not in varfuri_selectate:
                    varfuri_selectate = {varf_tras}
                anchor = obiect.varfuri[varf_tras, :3].copy()
                decalaje_tras = {
                    vi: obiect.varfuri[vi, :3] - anchor
                    for vi in varfuri_selectate
                }

        if varf_tras >= 0:
            if varf_tras in plan_varf:
                mx, my = event.pos
                cam_local = (inv_obiect @ np.array([0.0, 0.0, 0.0, 1.0]))[:3]
                ndc_rx =  (mx / WIDTH)  * 2.0 - 1.0
                ndc_ry = -(my / HEIGHT) * 2.0 + 1.0
                view_dir = np.array([ndc_rx / matrice_proiectie[0, 0],
                                     ndc_ry / matrice_proiectie[1, 1], -1.0, 0.0])
                local_dir = (inv_obiect @ view_dir)[:3]
                local_dir /= np.linalg.norm(local_dir)
                normal, d = plan_varf[varf_tras]
                denom = np.dot(normal, local_dir)
                if abs(denom) > 1e-8:
                    t = (d - np.dot(normal, cam_local)) / denom
                    if t > 0:
                        new_anchor = cam_local + local_dir * t
                        delta = new_anchor - obiect.varfuri[varf_tras, :3]
                        for vi in varfuri_selectate:
                            obiect.varfuri[vi, :3] += delta
                        recalculeaza_transformari = True
            else:
                dx_px, dy_px = event.rel
                clip_w  = float(varfuri_clip[varf_tras, 3])
                view_dx = (dx_px  / (WIDTH  * 0.5)) * clip_w / matrice_proiectie[0, 0]
                view_dy = (-dy_px / (HEIGHT * 0.5)) * clip_w / matrice_proiectie[1, 1]
                local_delta = inv_obiect @ np.array([view_dx, view_dy, 0.0, 0.0])
                for vi in varfuri_selectate:
                    obiect.muta_varf(vi,
                                          float(local_delta[0]),
                                          float(local_delta[1]),
                                          float(local_delta[2]))
                recalculeaza_transformari = True

    def proceseaza_mouse_up_edit(event: pygame.event.Event) -> None:
        nonlocal numar_varfuri, recalculeaza_transformari, varf_tras, pick_in_asteptare
        nonlocal decalaje_tras, pozitie_mouse_apasat, are_pozitie_mouse_apasat

        mx, my = event.pos
        mouse_down_pos = pozitie_mouse_apasat
        if are_pozitie_mouse_apasat:
            mdx = float(mouse_down_pos[0])
            mdy = float(mouse_down_pos[1])
            was_click = np.hypot(mx - mdx, my - mdy) <= CLICK_THRESH_PX
        else:
            was_click = False
        if was_click:
            if pick_in_asteptare >= 0:
                if pick_in_asteptare in fete_selectate:
                    fete_selectate.remove(pick_in_asteptare)
                elif len(fete_selectate) < 3:
                    fete_selectate.append(pick_in_asteptare)
            else:
                cam_origin_local = (inv_obiect @ np.array([0.0, 0.0, 0.0, 1.0]))[:3]
                ndc_rx =  (mx / WIDTH)  * 2.0 - 1.0
                ndc_ry = -(my / HEIGHT) * 2.0 + 1.0
                view_dir = np.array([ndc_rx / matrice_proiectie[0, 0],
                                     ndc_ry / matrice_proiectie[1, 1], -1.0, 0.0])
                local_dir = (inv_obiect @ view_dir)[:3]
                local_dir /= np.linalg.norm(local_dir)
                hit = raza(cam_origin_local, local_dir,
                           obiect.varfuri, obiect.fete)
                if hit is not None:
                    _, fi, hit_pt = hit
                    new_vi = obiect.adauga_varf(*hit_pt.tolist())
                    fata = obiect.fete[fi]
                    v0 = obiect.varfuri[fata[0], :3]
                    v1 = obiect.varfuri[fata[1], :3]
                    v2 = obiect.varfuri[fata[2], :3]
                    normal = np.cross(v1 - v0, v2 - v0)
                    nl = np.linalg.norm(normal)
                    if nl > 1e-8:
                        normal /= nl
                    plan_varf[new_vi] = (normal, float(np.dot(normal, v0)))
                elif plasare_libera:
                    avg_vz = float(np.mean(varfuri_lume[:, 2]))
                    lx, ly, lz = deproiecteaza_ecran(mx, my, avg_vz, matrice_proiectie, inv_obiect)
                    new_vi = obiect.adauga_varf(lx, ly, lz)
                else:
                    new_vi = -1
                if new_vi >= 0:
                    numar_varfuri = len(obiect.varfuri)
                    if len(fete_selectate) < 3:
                        fete_selectate.append(new_vi)
                    recalculeaza_transformari = True

        varf_tras = pick_in_asteptare = -1
        decalaje_tras.clear()
        pozitie_mouse_apasat = None
        are_pozitie_mouse_apasat = False

    def actualizeaza_miscare_continua() -> None:
        nonlocal pitch, yaw, roll, tx, ty, tz, cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw
        nonlocal recalculeaza_transformari

        keys        = pygame.key.get_pressed()
        rot_step    = np.radians(90.0) * dt
        move_step   = 3.0 * dt
        shift       = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        old = (pitch, yaw, roll, tx, ty, tz, cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw)

        if camera_mode:
            if keys[pygame.K_UP]:    cam_pitch -= rot_step
            if keys[pygame.K_DOWN]:  cam_pitch += rot_step
            if keys[pygame.K_LEFT]:  cam_yaw   -= rot_step
            if keys[pygame.K_RIGHT]: cam_yaw   += rot_step
            fwd   = np.array([ np.sin(cam_yaw)*np.cos(cam_pitch),
                               -np.sin(cam_pitch),
                               -np.cos(cam_yaw)*np.cos(cam_pitch)])
            right = np.array([np.cos(cam_yaw), 0.0, np.sin(cam_yaw)])
            up    = np.array([0.0, 1.0, 0.0])
            if keys[pygame.K_w]:
                if shift:
                    cam_tx += fwd[0]*move_step; cam_ty += fwd[1]*move_step; cam_tz += fwd[2]*move_step
                else:
                    cam_tx += up[0]*move_step;  cam_ty += up[1]*move_step;  cam_tz += up[2]*move_step
            if keys[pygame.K_s]:
                if shift:
                    cam_tx -= fwd[0]*move_step; cam_ty -= fwd[1]*move_step; cam_tz -= fwd[2]*move_step
                else:
                    cam_tx -= up[0]*move_step;  cam_ty -= up[1]*move_step;  cam_tz -= up[2]*move_step
            if keys[pygame.K_a]:
                cam_tx -= right[0]*move_step; cam_ty -= right[1]*move_step; cam_tz -= right[2]*move_step
            if keys[pygame.K_d]:
                cam_tx += right[0]*move_step; cam_ty += right[1]*move_step; cam_tz += right[2]*move_step
        else:
            if keys[pygame.K_UP]:    pitch -= rot_step
            if keys[pygame.K_DOWN]:  pitch += rot_step
            if keys[pygame.K_LEFT]:  yaw   -= rot_step
            if keys[pygame.K_RIGHT]: yaw   += rot_step
            if keys[pygame.K_w]:
                if shift: tz -= move_step
                else:     ty += move_step
            if keys[pygame.K_s]:
                if shift: tz += move_step
                else:     ty -= move_step
            if keys[pygame.K_a]: tx -= move_step
            if keys[pygame.K_d]: tx += move_step

        if (pitch, yaw, roll, tx, ty, tz, cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw) != old:
            recalculeaza_transformari = True

    def recalculeaza_pipeline() -> None:
        nonlocal transformare_obiect, inv_obiect, varfuri_lume, varfuri_clip, puncte_ecran, puncte_ecran_i
        nonlocal indici_fete_sortate, medie_z_sortata, nuante_fete, indici_fete_xray, nuante_xray
        nonlocal recalculeaza_transformari

        model_mat = compune(
            rotatie_x(pitch), rotatie_y(yaw), rotatie_z(roll),
            translatie(tx, ty, tz),
        )
        view_mat  = construieste_vizualizare(cam_tx, cam_ty, cam_tz, cam_pitch, cam_yaw)
        transformare_obiect = view_mat @ model_mat
        obiect.seteaza_transformare(transformare_obiect)
        inv_obiect = np.linalg.inv(transformare_obiect)

        varfuri_lume  = obiect.obtine_varfuri_lume()
        varfuri_clip   = (matrice_proiectie @ varfuri_lume.T).T
        w            = varfuri_clip[:, 3:4]
        safe_w       = np.where(np.abs(w) < 1e-7, 1e-7, w)
        ndc          = varfuri_clip[:, :3] / safe_w
        puncte_ecran   = ndc_la_ecran(ndc[:, 0], ndc[:, 1])
        puncte_ecran_i = puncte_ecran.astype(np.int32)

        f = obiect.fete
        if len(f) > 0:
            vs = varfuri_lume[:, :3]

            p0s   = puncte_ecran[f[:, 0]]
            p1s   = puncte_ecran[f[:, 1]]
            p2s   = puncte_ecran[f[:, 2]]
            areas = ((p1s[:,0]-p0s[:,0])*(p2s[:,1]-p0s[:,1]) -
                     (p1s[:,1]-p0s[:,1])*(p2s[:,0]-p0s[:,0]))
            front = np.where(areas <= 0)[0]

            e1_all = vs[f[:, 1]] - vs[f[:, 0]]
            e2_all = vs[f[:, 2]] - vs[f[:, 0]]
            normals_all = np.cross(e1_all, e2_all)
            nl_all = np.linalg.norm(normals_all, axis=1, keepdims=True)
            nl_all = np.where(nl_all < 1e-8, 1e-8, nl_all)
            normals_all /= nl_all

            LIGHT = np.array([0.4, 0.6, 0.8], dtype=np.float64)
            LIGHT /= np.linalg.norm(LIGHT)

            normals_front = normals_all[front]
            dot_front = np.clip(normals_front @ LIGHT, 0.0, 1.0)
            shades = dot_front * 0.75 + 0.25

            dot = np.abs(normals_all @ LIGHT)
            xray_shades_all = np.clip(0.10 + 0.90 * dot, 0.0, 1.0)

            avg_z    = (varfuri_clip[f[front,0],2] +
                        varfuri_clip[f[front,1],2] +
                        varfuri_clip[f[front,2],2]) / 3.0
            order       = np.argsort(avg_z)[::-1]
            indici_fete_sortate   = front[order]
            medie_z_sortata = avg_z[order]
            nuante_fete = shades[order]

            avg_z_all  = (varfuri_clip[f[:,0],2] +
                          varfuri_clip[f[:,1],2] +
                          varfuri_clip[f[:,2],2]) / 3.0
            xray_order  = np.argsort(avg_z_all)[::-1]
            indici_fete_xray     = xray_order
            nuante_xray = xray_shades_all[xray_order]
        else:
            indici_fete_sortate   = np.empty(0, dtype=np.int64)
            medie_z_sortata = np.empty(0, dtype=np.float64)
            nuante_fete = np.empty(0, dtype=np.float64)
            indici_fete_xray     = np.empty(0, dtype=np.int64)
            nuante_xray = np.empty(0, dtype=np.float64)

        recalculeaza_transformari = False

    def deseneaza_scena() -> None:
        ecran.fill(BG_COLOR)

        fill_c = FACE_COLOR_EDIT if editare_varfuri else FACE_COLOR

        if mod_randare == 2:
            for i, fi in enumerate(indici_fete_sortate):
                fata = obiect.fete[fi]
                puncte = [puncte_ecran_i[vi].tolist() for vi in fata]
                s = float(nuante_fete[i])
                pygame.draw.polygon(ecran,
                    (int(fill_c[0]*s), int(fill_c[1]*s), int(fill_c[2]*s)), puncte)

        elif mod_randare == 1:
            xray_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for idx, fi in enumerate(indici_fete_xray):
                fata = obiect.fete[fi]
                puncte = [puncte_ecran_i[vi].tolist() for vi in fata]
                s = float(nuante_xray[idx])
                col = (int(fill_c[0]*s), int(fill_c[1]*s), int(fill_c[2]*s), 60)
                pygame.draw.polygon(xray_surf, col, puncte)
                pygame.draw.polygon(xray_surf, (*WIRE_COLOR, 70), puncte, 1)
            ecran.blit(xray_surf, (0, 0))

        if afisare_triunghiuri and len(obiect.fete) > 0:
            triunghiuri_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for fata in obiect.fete:
                puncte = [puncte_ecran_i[int(vi)].tolist() for vi in fata]
                pygame.draw.polygon(triunghiuri_surf, (*TRIANGLE_COLOR, 160), puncte, 1)
            ecran.blit(triunghiuri_surf, (0, 0))

        if obiect.muchii is not None and (mod_randare < 2 or editare_varfuri):
            wire_c = EDIT_WIRE if editare_varfuri else WIRE_COLOR
            for muchie in obiect.muchii:
                pygame.draw.line(ecran, wire_c,
                                 puncte_ecran_i[int(muchie[0])].tolist(),
                                 puncte_ecran_i[int(muchie[1])].tolist(), 1)

        if editare_varfuri:
            if len(fete_selectate) >= 2:
                for k in range(len(fete_selectate) - 1):
                    pygame.draw.line(ecran, SEL_COLOR,
                                     puncte_ecran_i[fete_selectate[k]].tolist(),
                                     puncte_ecran_i[fete_selectate[k+1]].tolist(), 2)
                if len(fete_selectate) == 3:
                    pygame.draw.line(ecran, SEL_COLOR,
                                     puncte_ecran_i[fete_selectate[2]].tolist(),
                                     puncte_ecran_i[fete_selectate[0]].tolist(), 2)
                    pygame.draw.polygon(ecran, SEL_COLOR,
                                        [puncte_ecran_i[v].tolist() for v in fete_selectate], 2)

            mx, my   = pygame.mouse.get_pos()
            dists    = np.hypot(puncte_ecran[:, 0] - mx, puncte_ecran[:, 1] - my)
            hover_vi = int(np.argmin(dists)) if dists.min() < PICK_RADIUS_PX else -1

            for vi in range(numar_varfuri):
                is_special = (vi == varf_tras or vi in varfuri_selectate
                              or vi in fete_selectate or vi == hover_vi)
                if doar_varfuri_hover and not is_special:
                    continue
                pt = (int(puncte_ecran_i[vi, 0]), int(puncte_ecran_i[vi, 1]))
                if vi == varf_tras:
                    pygame.draw.circle(ecran, (255, 255,   0), pt, 7)
                    pygame.draw.circle(ecran, (255, 255, 255), pt, 7, 1)
                elif vi in varfuri_selectate:
                    pygame.draw.circle(ecran, HIGHLIGHT,       pt, 7)
                    pygame.draw.circle(ecran, (255, 255, 255), pt, 7, 1)
                elif vi in fete_selectate:
                    pygame.draw.circle(ecran, SEL_COLOR,       pt, 6)
                    pygame.draw.circle(ecran, (255, 255, 255), pt, 6, 1)
                elif vi == hover_vi:
                    pygame.draw.circle(ecran, (180, 180, 180), pt, 5)
                else:
                    pygame.draw.circle(ecran, (80,  80,  80),  pt, 3)

        deseneaza_hud(
            ecran,
            font,
            suprafata_hud,
            camera_mode,
            cam_tx,
            cam_ty,
            cam_tz,
            cam_pitch,
            cam_yaw,
            pitch,
            yaw,
            tx,
            ty,
            tz,
            editare_varfuri,
            varfuri_selectate,
            plasare_libera,
            fete_selectate,
            numar_varfuri,
            obiect,
            mod_randare,
            doar_varfuri_hover,
            afisare_triunghiuri,
            afisare_ajutor,
            mesaj_stare,
            timer_stare,
        )

    running = True
    while running:
        dt = ceas.tick(FPS) / 1000.0
        if timer_stare > 0:
            timer_stare = max(0.0, timer_stare - dt)

        # ------------------------------------------------------------------ #
        #  Evenimente                                                          #
        # ------------------------------------------------------------------ #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                proceseaza_keydown(event)

            # logica de selectare vârf, cu multi selecție dacă s-a apăsat ctrl, și pregătește posibilitatea de drag (dar nu mută nimic)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and editare_varfuri:
                proceseaza_mouse_down_edit(event)

            # logica de drag a vârfului sau vârfurilor, și îl mută liber sau pe planul constrâns
            elif event.type == pygame.MOUSEMOTION and editare_varfuri:
                proceseaza_mouse_motion_edit(event)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and editare_varfuri:
                proceseaza_mouse_up_edit(event)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                varf_tras = pick_in_asteptare = -1
                decalaje_tras.clear()
                pozitie_mouse_apasat = None
                are_pozitie_mouse_apasat = False

        # ------------------------------------------------------------------ #
        #  Taste continue                                                      #
        # ------------------------------------------------------------------ #
        actualizeaza_miscare_continua()

        # ------------------------------------------------------------------ #
        #  Pipeline (doar când e modificat)                                   #
        # ------------------------------------------------------------------ #
        if recalculeaza_transformari:
            recalculeaza_pipeline()

        # ------------------------------------------------------------------ #
        #  Randare                                                             #
        # ------------------------------------------------------------------ #
        deseneaza_scena()

        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    ecran = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Program de Modelare 3D")
    ceas = pygame.time.Clock()
    while True:
        main(ecran, ceas)
        pygame.event.clear()
