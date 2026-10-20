#!/usr/bin/env python3
"""Generates the "Director" CLEO script source (director.txt).

    python3 mods/director/gen_director.py en > mods/director/director.txt
    python3 mods/director/gen_director.py ru > mods/director/director_ru.txt

The script targets GTA SA Android 2.00 + CLEO Mod for AML 2.0.1.5.
Input uses the 9 CLEO touch zones (0DE0); every zone has an on-screen
button drawn at the screen edge:

      1   4   7
      2  (5)  8        5 (centre) is left free for the picture,
      3   6   9        it is only used as "MENU" on the camera page.
"""
import sys
from contextlib import contextmanager

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"

# ------------------------------------------------------------------ texts
# key: (english, russian); keys are GXT labels (max 7 chars, not "CL...")
TEXTS = {
    # main page
    "DTITLE": ("DIRECTOR", "РЕЖИССЁР"),
    "DB_CAM": ("CAMERA", "КАМЕРА"),
    "DB_SHT": ("SHOTS", "КАДРЫ"),
    "DB_ACT": ("ACTORS", "АКТЁРЫ"),
    "DB_WLD": ("WORLD", "МИР"),
    "DB_PLAY": ("PLAY SCENE", "МОТОР!"),
    "DB_ADD": ("+ SHOT", "+ КАДР"),
    "DB_HIDE": ("HIDE MENU", "СКРЫТЬ МЕНЮ"),
    "DB_EXIT": ("EXIT", "ВЫХОД"),
    "DB_SURE": ("TAP AGAIN", "ЕЩЁ РАЗ"),
    "DB_BACK": ("BACK", "НАЗАД"),
    "DB_MORE": ("MORE", "ЕЩЁ"),
    "DB_MENU": ("MENU", "МЕНЮ"),
    # camera page
    "DC_FWD": ("FORWARD", "ВПЕРЁД"),
    "DC_BCK": ("BACK", "НАЗАД"),
    "DC_TL": ("TURN LEFT", "ВЛЕВО"),
    "DC_TR": ("TURN RIGHT", "ВПРАВО"),
    "DC_UP": ("UP", "ВВЕРХ"),
    "DC_DN": ("DOWN", "ВНИЗ"),
    "DC_PU": ("TILT UP", "НАКЛОН ВВЕРХ"),
    "DC_PD": ("TILT DOWN", "НАКЛОН ВНИЗ"),
    # shots pages
    "DS_ADD": ("+ SHOT", "+ КАДР"),
    "DS_CUT": ("+ CUT", "+ СКЛЕЙКА"),
    "DS_DEL": ("DELETE", "УДАЛИТЬ"),
    "DS_PRV": ("PREV", "ПРЕДЫДУЩИЙ"),
    "DS_NXT": ("NEXT", "СЛЕДУЮЩИЙ"),
    "DS_TP": ("TIME +", "ВРЕМЯ +"),
    "DS_TM": ("TIME -", "ВРЕМЯ -"),
    "DS_TYP": ("SMOOTH / CUT", "ПЛАВНО / СКЛЕЙКА"),
    "DS_ZI": ("ZOOM IN", "ЗУМ +"),
    "DS_ZO": ("ZOOM OUT", "ЗУМ -"),
    "DS_UPD": ("UPDATE", "ПЕРЕСНЯТЬ"),
    "DS_CLR": ("CLEAR ALL", "УДАЛИТЬ ВСЁ"),
    "DS_NONE": ("NO SHOTS YET", "КАДРОВ ПОКА НЕТ"),
    "DS_NUM": ("SHOT ~1~ OF ~1~", "КАДР ~1~ ИЗ ~1~"),
    "DS_SM": ("SMOOTH  ~1~.~1~ SEC", "ПЛАВНО  ~1~.~1~ СЕК"),
    "DS_CT": ("CUT  ~1~.~1~ SEC", "СКЛЕЙКА  ~1~.~1~ СЕК"),
    "DS_CNT": ("SHOTS: ~1~", "КАДРОВ: ~1~"),
    # actors pages
    "DA_ADD": ("+ ACTOR", "+ АКТЁР"),
    "DA_MOD": ("MODEL", "МОДЕЛЬ"),
    "DA_DEL": ("DELETE", "УДАЛИТЬ"),
    "DA_SEL": ("SELECT", "ВЫБРАТЬ"),
    "DA_ANX": ("ANIM +", "АНИМАЦИЯ +"),
    "DA_ANP": ("ANIM -", "АНИМАЦИЯ -"),
    "DA_WLK": ("WALK HERE", "ИДТИ СЮДА"),
    "DA_RUN": ("RUN HERE", "БЕЖАТЬ СЮДА"),
    "DA_STP": ("STOP", "СТОП"),
    "DA_FCE": ("FACE EACH OTHER", "ДРУГ НА ДРУГА"),
    "DA_LKC": ("LOOK AT CAMERA", "В КАМЕРУ"),
    "DA_CJ": ("SELECTED: CJ", "ВЫБРАН: CJ"),
    "DA_NUM": ("SELECTED: ACTOR ~1~", "ВЫБРАН: АКТЁР ~1~"),
    "DA_NOAN": ("ANIM: -", "АНИМАЦИЯ: -"),
    # world page
    "DW_HP": ("HOUR +", "ЧАС +"),
    "DW_HM": ("HOUR -", "ЧАС -"),
    "DW_WTH": ("WEATHER", "ПОГОДА"),
    "DW_SLO": ("SLOW-MO", "ЗАМЕДЛЕНИЕ"),
    "DW_BR0": ("BARS: OFF", "ПОЛОСЫ: ВЫКЛ"),
    "DW_BR1": ("BARS: ON", "ПОЛОСЫ: ВКЛ"),
    "DW_EM0": ("EMPTY STREETS: OFF", "ПУСТЫЕ УЛИЦЫ: ВЫКЛ"),
    "DW_EM1": ("EMPTY STREETS: ON", "ПУСТЫЕ УЛИЦЫ: ВКЛ"),
    "DW_CJ0": ("HIDE CJ", "СКРЫТЬ CJ"),
    "DW_CJ1": ("SHOW CJ", "ПОКАЗАТЬ CJ"),
    "DW_TIM": ("TIME ~1~:00   WEATHER ~1~", "ВРЕМЯ ~1~:00   ПОГОДА ~1~"),
    "DW_S0": ("GAME SPEED 100%", "СКОРОСТЬ ИГРЫ 100%"),
    "DW_S1": ("GAME SPEED 50%", "СКОРОСТЬ ИГРЫ 50%"),
    "DW_S2": ("GAME SPEED 25%", "СКОРОСТЬ ИГРЫ 25%"),
}

# ped models for "MODEL": (model id or 0 = random, english, russian)
MODELS = [
    (0, "RANDOM", "СЛУЧАЙНЫЙ"),
    (105, "GROVE 1", "ГРУВ 1"),
    (106, "GROVE 2", "ГРУВ 2"),
    (107, "GROVE 3", "ГРУВ 3"),
    (102, "BALLAS 1", "БАЛЛАС 1"),
    (104, "BALLAS 2", "БАЛЛАС 2"),
    (108, "VAGOS", "ВАГОС"),
    (280, "POLICE", "ПОЛИЦИЯ"),
    (285, "SWAT", "СПЕЦНАЗ"),
    (286, "FBI", "ФБР"),
    (287, "ARMY", "АРМИЯ"),
    (274, "MEDIC", "МЕДИК"),
]

# animations: (anim, ifp, loop, keep last frame, english, russian)
ANIMS = [
    ("IDLE_chat", "PED", 1, 0, "TALK", "РАЗГОВОР"),
    ("phone_talk", "PED", 1, 0, "PHONE", "ТЕЛЕФОН"),
    ("IDLE_tired", "PED", 1, 0, "TIRED", "УСТАЛ"),
    ("handsup", "PED", 0, 1, "HANDS UP", "РУКИ ВВЕРХ"),
    ("cower", "PED", 1, 0, "SCARED", "ИСПУГ"),
    ("fucku", "PED", 0, 0, "RUDE", "НЕПРИЛИЧНЫЙ ЖЕСТ"),
    ("KO_shot_stom", "PED", 0, 1, "FALL", "ПАДАЕТ"),
    ("prtial_gngtlkA", "GANGS", 1, 0, "GANG TALK 1", "БАНДИТ ГОВОРИТ 1"),
    ("prtial_gngtlkB", "GANGS", 1, 0, "GANG TALK 2", "БАНДИТ ГОВОРИТ 2"),
    ("hndshkfa", "GANGS", 0, 0, "HANDSHAKE", "РУКОПОЖАТИЕ"),
    ("Invite_Yes", "GANGS", 0, 0, "YES", "ДА"),
    ("Invite_No", "GANGS", 0, 0, "NO", "НЕТ"),
    ("shout_01", "ON_LOOKERS", 1, 0, "SHOUT", "КРИЧИТ"),
    ("pointup_loop", "ON_LOOKERS", 1, 0, "POINT UP", "ПОКАЗЫВАЕТ ВВЕРХ"),
    ("wave_loop", "ON_LOOKERS", 1, 0, "WAVE", "МАШЕТ"),
    ("dnce_M_a", "DANCING", 1, 0, "DANCE", "ТАНЕЦ"),
]

MAX_SHOTS = 24
SHOT_SIZE = 32          # x y z heading pitch fov duration type
ACTORS_OFF = 800        # 6 actor handles
MAX_ACTORS = 6
SCRATCH = 900
MEM_SIZE = 1024

# ------------------------------------------------------------- variables
PLR, PAGE = "0@", "1@"
CX, CY, CZ, HD, PT, FOV = "2@", "3@", "4@", "5@", "6@", "7@"
F0, F1, F2, F3 = "8@", "9@", "10@", "11@"
T = "12@"        # touch result / temp / selected char handle
HL = "13@"       # zone drawn highlighted (0 = none)
MEM = "14@"      # allocated memory
CNT, SEL = "15@", "16@"
ZN = "17@"       # pressed zone
PI = "18@"       # playback index
TMP = "19@"
HELD = "20@"
SCH = "21@"      # selected character: 0 CJ, 1..6 actor slot
ANI, MOD, WTH, SLO, FLG = "22@", "23@", "24@", "25@", "26@"
EXC = "27@"      # 1 = exit armed, 2 = clear-all armed
HID = "28@"      # 1 = menu hidden
A, IDX, OUT = "29@", "30@", "31@"
TA, TB = "32@", "33@"

P_MAIN, P_CAM, P_SHOTS, P_SHOTS2, P_ACT, P_ACT2, P_WORLD = range(7)

out = []
_n = [0]


def e(*parts):
    out.append(" ".join(str(p) for p in parts))


def new(prefix="L"):
    _n[0] += 1
    return "%s_%d" % (prefix, _n[0])


def lab(name):
    e(":" + name)


@contextmanager
def iff(*conds, any_of=False):
    """Body runs when all (or any) conditions are true."""
    end = new()
    n = len(conds)
    e("IF", 0 if n == 1 else (20 + n - 1 if any_of else n - 1))
    for c in conds:
        e(c)
    e("GOTO_IF_FALSE @" + end)
    yield end
    lab(end)


def ifelse(conds, then_fn, else_fn, any_of=False):
    els, end = new(), new()
    n = len(conds)
    e("IF", 0 if n == 1 else (20 + n - 1 if any_of else n - 1))
    for c in conds:
        e(c)
    e("GOTO_IF_FALSE @" + els)
    then_fn()
    e("GOTO @" + end)
    lab(els)
    else_fn()
    lab(end)


def eq(var, val):
    return "IS_INT_LVAR_EQUAL_TO_NUMBER %s %s" % (var, val)


def touched(zone):
    e("GET_TOUCH_POINT_STATE", T, zone, 0)
    return eq(T, 1)


def text(key):
    t = TEXTS[key]
    s = t[1] if LANG == "ru" else t[0]
    return s


def fl(x):
    return "%.1f" % x if float(x).is_integer() else repr(float(x))


# ----------------------------------------------------------- UI geometry
POS = {1: (80, 70), 2: (80, 224), 3: (80, 378),
       7: (560, 70), 8: (560, 224), 9: (560, 378),
       4: (320, 30), 6: (320, 418), 5: (320, 224)}
SIZE = {1: (140, 44), 2: (140, 44), 3: (140, 44), 7: (140, 44), 8: (140, 44),
        9: (140, 44), 4: (180, 34), 6: (180, 34), 5: (90, 30)}


def text_style(scale_x, scale_y, r, g, b):
    e("SET_TEXT_FONT", 1)
    e("SET_TEXT_PROPORTIONAL", 1)
    e("SET_TEXT_SCALE", fl(scale_x), fl(scale_y))
    e("SET_TEXT_COLOUR", r, g, b, 255)
    e("SET_TEXT_CENTRE", 1)
    e("SET_TEXT_EDGE", 1, 0, 0, 0, 255)


def button(zone, key, faint=False):
    """Box + label at the edge position of a touch zone."""
    x, y = POS[zone]
    w, h = SIZE[zone]
    alpha = 70 if faint else 150

    def pressed():
        e("DRAW_RECT", fl(x), fl(y), fl(w), fl(h), 230, 150, 30, 210)

    def normal():
        e("DRAW_RECT", fl(x), fl(y), fl(w), fl(h), 0, 0, 0, alpha)
    ifelse([eq(HL, zone)], pressed, normal)
    sx, sy = (0.36, 1.45) if faint else (0.42, 1.7)
    text_style(sx, sy, 255, 255, 255)
    e("DISPLAY_TEXT", fl(x), fl(y - (6 if faint else 8)), "'%s'" % key)


def status_style():
    text_style(0.32, 1.3, 255, 210, 90)


STATUS_Y = (54, 70, 86)

# ================================================================ program
e("// GENERATED by mods/director/gen_director.py (%s) - do not edit" % LANG)
e("NOP")
e("SCRIPT_NAME 'DIRECTR'")
e("#ifdef CSA")
lab("ACTIVATE")
e("WAIT 100")
with iff("IS_PLAYER_PLAYING 0", "IS_PLAYER_CONTROL_ON 0"):
    e("GET_TOUCH_POINT_STATE", T, 4, 2000)
    with iff(eq(T, 1)):
        e("GOTO @ACT_RELEASE")
e("GOTO @ACTIVATE")
lab("ACT_RELEASE")      # wait until the activating finger is lifted
e("WAIT 0")
e("GET_TOUCH_POINT_STATE", T, 4, 0)
with iff(eq(T, 1)):
    e("GOTO @ACT_RELEASE")
e("#endif")

# ------------------------------------------------------------------ init
lab("INIT")
e("GET_PLAYER_CHAR 0", PLR)
for key in TEXTS:
    e("ADD_TEXT_LABEL", "'%s'" % key, '"%s"' % text(key))
for i, m in enumerate(MODELS):
    e("ADD_TEXT_LABEL", "'DM%d'" % i, '"%s"' % ((m[2] if LANG == "ru" else m[1])))
for i, a in enumerate(ANIMS):
    e("ADD_TEXT_LABEL", "'DN%d'" % i, '"%s"' % ((a[5] if LANG == "ru" else a[4])))
e("ALLOCATE_MEMORY", MEM_SIZE, MEM)
for i in range(MAX_ACTORS):
    e("SET_LVAR_INT_TO_LVAR_INT", A, MEM)
    e("ADD_VAL_TO_INT_LVAR", A, ACTORS_OFF + 4 * i)
    e("WRITE_MEMORY", A, -1, 4, 0, 0)
e("GET_ACTIVE_CAMERA_COORDINATES", CX, CY, CZ)
e("GET_ACTIVE_CAMERA_POINT_AT", F0, F1, F2)
e("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR", F0, CX)
e("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR", F1, CY)
e("GET_HEADING_FROM_VECTOR_2D", F0, F1, HD)
e("SET_LVAR_FLOAT", PT, "-5.0")
e("SET_LVAR_FLOAT", FOV, "70.0")
for v, val in ((PAGE, P_MAIN), (HL, 0), (CNT, 0), (SEL, 0), (SCH, 0), (ANI, -1),
               (MOD, 0), (WTH, 0), (SLO, 0), (FLG, 0), (EXC, 0), (HID, 0)):
    e("SET_LVAR_INT", v, val)
e("SET_PLAYER_CONTROL 0 0")
e("SET_EVERYONE_IGNORE_PLAYER 0 1")
e("SET_CHAR_PROOFS", PLR, "1 1 1 1 1")
e("DISPLAY_HUD 0")
e("DISPLAY_RADAR 0")
e("USE_TEXT_COMMANDS 1")
e("REQUEST_ANIMATION 'GANGS'")
e('REQUEST_ANIMATION "ON_LOOKERS"')
e("REQUEST_ANIMATION 'DANCING'")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
e("SET_LVAR_INT", TB, 0)

# ------------------------------------------------------------- main loop
lab("MAIN")
e("WAIT 0")
with iff("NOT IS_PLAYER_PLAYING 0"):
    e("GOTO @EXIT")
e("GOSUB @FOLLOW")
with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 0" % EXC, "IS_INT_LVAR_GREATER_THAN_NUMBER %s 3000" % TA):
    e("SET_LVAR_INT", EXC, 0)
with iff(eq(HID, 1)):
    e("GOSUB @GET_PRESSED")
    with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 0" % ZN):
        e("GOSUB @WAIT_RELEASE")
        e("SET_LVAR_INT", HID, 0)
    e("GOTO @MAIN_END")
for p, name in ((P_CAM, "PAGE_CAM"), (P_SHOTS2, "PAGE_SHOTS2")):
    with iff(eq(PAGE, p)):
        e("GOTO @" + name)
# tap pages: act on release of a zone
e("GOSUB @GET_PRESSED")
with iff(eq(ZN, 0)):
    e("GOTO @MAIN_END")
e("GOSUB @WAIT_RELEASE")
for p, name in ((P_MAIN, "PAGE_MAIN"), (P_SHOTS, "PAGE_SHOTS"), (P_ACT, "PAGE_ACT"),
                (P_ACT2, "PAGE_ACT2"), (P_WORLD, "PAGE_WORLD")):
    with iff(eq(PAGE, p)):
        e("GOTO @" + name)
lab("MAIN_END")
e("GOSUB @APPLY_CAM")
e("GOSUB @DRAW_UI")
e("GOTO @MAIN")


def on_zone(zone, body):
    with iff(eq(ZN, zone)):
        body()
        e("GOTO @MAIN_END")


def goto_page(p):
    return lambda: e("SET_LVAR_INT", PAGE, p)


# ----------------------------------------------------------- main page
lab("PAGE_MAIN")
on_zone(1, goto_page(P_CAM))
on_zone(2, goto_page(P_SHOTS))
on_zone(3, goto_page(P_ACT))
on_zone(7, goto_page(P_WORLD))
on_zone(8, lambda: e("GOSUB @PLAY_SCENE"))


def quick_add():
    e("SET_LVAR_INT", TMP, 0)
    e("GOSUB @ADD_SHOT")
on_zone(9, quick_add)
on_zone(4, lambda: e("SET_LVAR_INT", HID, 1))


def exit_tap():
    with iff(eq(EXC, 1)):
        e("GOTO @EXIT")
    e("SET_LVAR_INT", EXC, 1)
    e("SET_LVAR_INT", TA, 0)
on_zone(6, exit_tap)
e("GOTO @MAIN_END")

# ---------------------------------------------------------- camera page
lab("PAGE_CAM")
e("SET_LVAR_INT", HELD, 0)
e("CSET_LVAR_FLOAT_TO_LVAR_INT", F3, TB)
e("SET_LVAR_FLOAT_TO_LVAR_FLOAT", F0, F3)
e("MULT_FLOAT_LVAR_BY_VAL", F0, "0.0006")
e("ADD_VAL_TO_FLOAT_LVAR", F0, "0.3")
with iff("IS_FLOAT_LVAR_GREATER_THAN_NUMBER %s 2.5" % F0):
    e("SET_LVAR_FLOAT", F0, "2.5")
e("MULT_FLOAT_LVAR_BY_VAL", F3, "0.0004")
e("ADD_VAL_TO_FLOAT_LVAR", F3, "0.03")
with iff("IS_FLOAT_LVAR_GREATER_THAN_NUMBER %s 1.0" % F3):
    e("SET_LVAR_FLOAT", F3, "1.0")
e("SET_LVAR_INT", HL, 0)


def hold(zone, body):
    with iff(touched(zone)):
        body()
        e("SET_LVAR_INT", HELD, 1)
        e("SET_LVAR_INT", HL, zone)


hold(2, lambda: e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", HD, F0))
hold(8, lambda: e("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR", HD, F0))


def tilt(sign):
    def body():
        e("MULT_FLOAT_LVAR_BY_VAL", F0, "0.6")
        if sign > 0:
            e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", PT, F0)
            with iff("IS_FLOAT_LVAR_GREATER_THAN_NUMBER %s 85.0" % PT):
                e("SET_LVAR_FLOAT", PT, "85.0")
        else:
            e("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR", PT, F0)
            with iff("IS_NUMBER_GREATER_THAN_FLOAT_LVAR -85.0 %s" % PT):
                e("SET_LVAR_FLOAT", PT, "-85.0")
    return body


hold(7, tilt(1))
hold(9, tilt(-1))
e("GOSUB @CALC_DIR")
for v in (F0, F1, F2):
    e("MULT_FLOAT_LVAR_BY_FLOAT_LVAR", v, F3)


def move(op):
    def body():
        for c, d in ((CX, F0), (CY, F1), (CZ, F2)):
            e(op, c, d)
    return body


hold(4, move("ADD_FLOAT_LVAR_TO_FLOAT_LVAR"))
hold(6, move("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR"))
hold(1, lambda: e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", CZ, F3))
hold(3, lambda: e("SUB_FLOAT_LVAR_FROM_FLOAT_LVAR", CZ, F3))
with iff(eq(HELD, 0)):
    e("SET_LVAR_INT", TB, 0)
with iff(touched(5)):
    e("SET_LVAR_INT", ZN, 5)
    e("SET_LVAR_INT", HL, 5)
    e("GOSUB @WAIT_RELEASE")
    e("SET_LVAR_INT", PAGE, P_MAIN)
e("GOTO @MAIN_END")

# ----------------------------------------------------------- shots page
lab("PAGE_SHOTS")


def add_type(t):
    def body():
        e("SET_LVAR_INT", TMP, t)
        e("GOSUB @ADD_SHOT")
    return body


on_zone(1, add_type(0))
on_zone(2, add_type(1))
on_zone(3, lambda: e("GOSUB @DELETE_SHOT"))


def step(delta):
    def body():
        if delta < 0:
            with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 0" % SEL):
                e("SUB_VAL_FROM_INT_LVAR", SEL, 1)
        else:
            e("SET_LVAR_INT_TO_LVAR_INT", TMP, SEL)
            e("ADD_VAL_TO_INT_LVAR", TMP, 1)
            with iff("IS_INT_LVAR_GREATER_THAN_INT_LVAR %s %s" % (CNT, TMP)):
                e("SET_LVAR_INT_TO_LVAR_INT", SEL, TMP)
        e("GOSUB @PREVIEW_SHOT")
    return body


on_zone(7, step(-1))
on_zone(8, step(1))
on_zone(9, goto_page(P_SHOTS2))
on_zone(6, goto_page(P_CAM))
on_zone(4, goto_page(P_MAIN))
e("GOTO @MAIN_END")

# ---------------------------------------- shots page 2 (has zoom holds)
lab("PAGE_SHOTS2")
e("SET_LVAR_INT", HL, 0)
for zone, sign in ((7, -1), (8, 1)):
    def zoom(sign=sign, zone=zone):
        if sign < 0:
            e("SUB_VAL_FROM_FLOAT_LVAR", FOV, "0.4")
            with iff("IS_NUMBER_GREATER_THAN_FLOAT_LVAR 10.0 %s" % FOV):
                e("SET_LVAR_FLOAT", FOV, "10.0")
        else:
            e("ADD_VAL_TO_FLOAT_LVAR", FOV, "0.4")
            with iff("IS_FLOAT_LVAR_GREATER_THAN_NUMBER %s 100.0" % FOV):
                e("SET_LVAR_FLOAT", FOV, "100.0")
        e("GOSUB @APPLY_FOV")
        e("SET_LVAR_INT", HL, zone)
        e("GOTO @MAIN_END")
    with iff(touched(zone)):
        zoom()
e("GOSUB @GET_PRESSED")
with iff(eq(ZN, 0)):
    e("GOTO @MAIN_END")
e("GOSUB @WAIT_RELEASE")


def change_time(delta):
    def body():
        with iff(eq(CNT, 0)):
            e("GOTO @MAIN_END")
        e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
        e("GOSUB @GET_SHOT_DUR")
        if delta > 0:
            e("ADD_VAL_TO_INT_LVAR", OUT, delta)
            with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 60000" % OUT):
                e("SET_LVAR_INT", OUT, 60000)
        else:
            e("SUB_VAL_FROM_INT_LVAR", OUT, -delta)
            with iff("IS_NUMBER_GREATER_THAN_INT_LVAR 500 %s" % OUT):
                e("SET_LVAR_INT", OUT, 500)
        e("GOSUB @SET_SHOT_DUR")
    return body


on_zone(1, change_time(500))
on_zone(2, change_time(-500))


def toggle_type():
    with iff(eq(CNT, 0)):
        e("GOTO @MAIN_END")
    e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
    e("GOSUB @GET_SHOT_TYPE")
    ifelse([eq(OUT, 0)], lambda: e("SET_LVAR_INT", OUT, 1), lambda: e("SET_LVAR_INT", OUT, 0))
    e("GOSUB @SET_SHOT_TYPE")


on_zone(3, toggle_type)


def update_shot():
    with iff(eq(CNT, 0)):
        e("GOTO @MAIN_END")
    e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
    e("GOSUB @SAVE_SHOT_CAM")


on_zone(9, update_shot)


def clear_all():
    with iff(eq(EXC, 2)):
        e("SET_LVAR_INT", CNT, 0)
        e("SET_LVAR_INT", SEL, 0)
        e("SET_LVAR_INT", EXC, 0)
        e("GOTO @MAIN_END")
    e("SET_LVAR_INT", EXC, 2)
    e("SET_LVAR_INT", TA, 0)


on_zone(6, clear_all)
on_zone(4, goto_page(P_SHOTS))
e("GOTO @MAIN_END")

# ---------------------------------------------------------- actors pages
lab("PAGE_ACT")
on_zone(1, lambda: e("GOSUB @SPAWN_ACTOR"))


def next_model():
    e("ADD_VAL_TO_INT_LVAR", MOD, 1)
    with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s %d" % (MOD, len(MODELS) - 1)):
        e("SET_LVAR_INT", MOD, 0)


on_zone(2, next_model)
on_zone(3, lambda: e("GOSUB @DELETE_ACTOR"))
on_zone(7, lambda: e("GOSUB @SELECT_NEXT"))


def anim_step(delta):
    def body():
        if delta > 0:
            e("ADD_VAL_TO_INT_LVAR", ANI, 1)
            with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s %d" % (ANI, len(ANIMS) - 1)):
                e("SET_LVAR_INT", ANI, 0)
        else:
            e("SUB_VAL_FROM_INT_LVAR", ANI, 1)
            with iff("IS_NUMBER_GREATER_THAN_INT_LVAR 0 %s" % ANI):
                e("SET_LVAR_INT", ANI, len(ANIMS) - 1)
        e("GOSUB @GET_SEL")
        e("GOSUB @PLAY_ANIM")
    return body


on_zone(8, anim_step(1))
on_zone(6, anim_step(-1))
on_zone(9, goto_page(P_ACT2))
on_zone(4, goto_page(P_MAIN))
e("GOTO @MAIN_END")

lab("PAGE_ACT2")


def with_sel(body):
    def run():
        e("GOSUB @GET_SEL")
        with iff("NOT IS_INT_LVAR_EQUAL_TO_NUMBER %s -1" % T):
            body()
    return run


def walk(speed):
    def body():
        e("GOSUB @POINT_AHEAD")
        e("TASK_GO_STRAIGHT_TO_COORD", T, F0, F1, F2, speed, 20000)
    return body


on_zone(1, with_sel(walk(4)))
on_zone(2, with_sel(walk(6)))
on_zone(3, with_sel(lambda: e("CLEAR_CHAR_TASKS", T)))
on_zone(7, lambda: e("GOSUB @FACE_EACH_OTHER"))
on_zone(8, with_sel(lambda: e("TASK_TURN_CHAR_TO_FACE_COORD", T, CX, CY, CZ)))
on_zone(9, lambda: e("GOSUB @SELECT_NEXT"))
on_zone(4, goto_page(P_ACT))
e("GOTO @MAIN_END")

# ------------------------------------------------------------ world page
lab("PAGE_WORLD")


def hour(delta):
    def body():
        e("GET_TIME_OF_DAY", TMP, OUT)
        if delta > 0:
            e("ADD_VAL_TO_INT_LVAR", TMP, 1)
            with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 23" % TMP):
                e("SET_LVAR_INT", TMP, 0)
        else:
            e("SUB_VAL_FROM_INT_LVAR", TMP, 1)
            with iff("IS_NUMBER_GREATER_THAN_INT_LVAR 0 %s" % TMP):
                e("SET_LVAR_INT", TMP, 23)
        e("SET_TIME_OF_DAY", TMP, 0)
    return body


on_zone(1, hour(1))
on_zone(2, hour(-1))


def weather():
    e("ADD_VAL_TO_INT_LVAR", WTH, 1)
    with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 19" % WTH):
        e("SET_LVAR_INT", WTH, 0)
    e("FORCE_WEATHER_NOW", WTH)


on_zone(3, weather)


def slowmo():
    e("ADD_VAL_TO_INT_LVAR", SLO, 1)
    with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 2" % SLO):
        e("SET_LVAR_INT", SLO, 0)
    for i, sc in enumerate(("1.0", "0.5", "0.25")):
        with iff(eq(SLO, i)):
            e("SET_TIME_SCALE", sc)


on_zone(7, slowmo)
on_zone(8, lambda: e("GOSUB @TOGGLE_WIDE"))
on_zone(9, lambda: e("GOSUB @TOGGLE_EMPTY"))
on_zone(6, lambda: e("GOSUB @TOGGLE_HIDE"))
on_zone(4, goto_page(P_MAIN))
e("GOTO @MAIN_END")

# ============================================================ subroutines
# ZN = first touched zone (0 = none)
lab("GET_PRESSED")
for z in (1, 2, 3, 4, 6, 7, 8, 9, 5):
    with iff(touched(z)):
        e("SET_LVAR_INT", ZN, z)
        e("RETURN")
e("SET_LVAR_INT", ZN, 0)
e("RETURN")

# keeps drawing the menu (zone ZN highlighted) until the finger is lifted
lab("WAIT_RELEASE")
e("SET_LVAR_INT_TO_LVAR_INT", HL, ZN)
lab("WR_LOOP")
e("WAIT 0")
e("GOSUB @DRAW_UI")
e("GET_TOUCH_POINT_STATE", T, ZN, 0)
with iff(eq(T, 1)):
    e("GOTO @WR_LOOP")
e("SET_LVAR_INT", HL, 0)
e("RETURN")

# F0 F1 F2 = unit view direction
lab("CALC_DIR")
e("COS", PT, F2)
e("SIN", HD, F0)
e("MULT_FLOAT_LVAR_BY_VAL", F0, "-1.0")
e("MULT_FLOAT_LVAR_BY_FLOAT_LVAR", F0, F2)
e("COS", HD, F1)
e("MULT_FLOAT_LVAR_BY_FLOAT_LVAR", F1, F2)
e("SIN", PT, F2)
e("RETURN")

# F0 F1 F2 = point 5 m in front of the camera
lab("CALC_TARGET")
e("GOSUB @CALC_DIR")
for v, c in ((F0, CX), (F1, CY), (F2, CZ)):
    e("MULT_FLOAT_LVAR_BY_VAL", v, "5.0")
    e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", v, c)
e("RETURN")

lab("APPLY_CAM")
e("GOSUB @CALC_TARGET")
e("SET_FIXED_CAMERA_POSITION", CX, CY, CZ, "0.0 0.0 0.0")
e("POINT_CAMERA_AT_POINT", F0, F1, F2, 2)
e("RETURN")

lab("APPLY_FOV")
e("CAMERA_SET_LERP_FOV", FOV, FOV, 100, 0)
e("CAMERA_PERSIST_FOV 1")
e("RETURN")

# F0 F1 F2 = ground point 6 m in front of the camera
lab("POINT_AHEAD")
e("SIN", HD, F0)
e("MULT_FLOAT_LVAR_BY_VAL", F0, "-6.0")
e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", F0, CX)
e("COS", HD, F1)
e("MULT_FLOAT_LVAR_BY_VAL", F1, "6.0")
e("ADD_FLOAT_LVAR_TO_FLOAT_LVAR", F1, CY)
e("GET_GROUND_Z_FOR_3D_COORD", F0, F1, CZ, F2)
e("RETURN")

# ------------------------------------------------------------ shot memory
# shot IDX: x y z heading pitch fov (floats), duration ms, type (0 smooth, 1 cut)
lab("SHOT_PTR")
e("SET_LVAR_INT_TO_LVAR_INT", A, IDX)
e("MULT_INT_LVAR_BY_VAL", A, SHOT_SIZE)
e("ADD_INT_LVAR_TO_INT_LVAR", A, MEM)
e("RETURN")

lab("LOAD_SHOT")
e("GOSUB @SHOT_PTR")
for v in (CX, CY, CZ, HD, PT, FOV):
    e("READ_MEMORY", v, A, 4, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
e("RETURN")

lab("SAVE_SHOT_CAM")
e("GOSUB @SHOT_PTR")
for v in (CX, CY, CZ, HD, PT, FOV):
    e("WRITE_MEMORY", A, v, 4, 0, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
e("RETURN")

for name, off, write in (("GET_SHOT_DUR", 24, False), ("SET_SHOT_DUR", 24, True),
                         ("GET_SHOT_TYPE", 28, False), ("SET_SHOT_TYPE", 28, True)):
    lab(name)
    e("GOSUB @SHOT_PTR")
    e("ADD_VAL_TO_INT_LVAR", A, off)
    if write:
        e("WRITE_MEMORY", A, OUT, 4, 0, 0)
    else:
        e("READ_MEMORY", OUT, A, 4, 0)
    e("RETURN")

# new shot from the current camera, type in TMP
lab("ADD_SHOT")
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s %d" % (CNT, MAX_SHOTS)):
    e("RETURN")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, CNT)
e("GOSUB @SAVE_SHOT_CAM")
e("SET_LVAR_INT", OUT, 3000)
e("GOSUB @SET_SHOT_DUR")
e("SET_LVAR_INT_TO_LVAR_INT", OUT, TMP)
with iff(eq(CNT, 0)):
    e("SET_LVAR_INT", OUT, 1)
e("GOSUB @SET_SHOT_TYPE")
e("SET_LVAR_INT_TO_LVAR_INT", SEL, CNT)
e("ADD_VAL_TO_INT_LVAR", CNT, 1)
e("RETURN")

lab("DELETE_SHOT")
with iff(eq(CNT, 0)):
    e("RETURN")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
e("GOSUB @SHOT_PTR")
e("SET_LVAR_INT_TO_LVAR_INT", TMP, CNT)
e("SUB_VAL_FROM_INT_LVAR", TMP, 1)
e("MULT_INT_LVAR_BY_VAL", TMP, SHOT_SIZE)
e("ADD_INT_LVAR_TO_INT_LVAR", TMP, MEM)
lab("DS_LOOP")
with iff("IS_INT_LVAR_GREATER_THAN_INT_LVAR %s %s" % (TMP, A)):
    e("SET_LVAR_INT_TO_LVAR_INT", IDX, A)
    e("ADD_VAL_TO_INT_LVAR", IDX, SHOT_SIZE)
    e("READ_MEMORY", OUT, IDX, 4, 0)
    e("WRITE_MEMORY", A, OUT, 4, 0, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
    e("GOTO @DS_LOOP")
e("SUB_VAL_FROM_INT_LVAR", CNT, 1)
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_INT_LVAR %s %s" % (SEL, CNT)):
    e("SET_LVAR_INT_TO_LVAR_INT", SEL, CNT)
    e("SUB_VAL_FROM_INT_LVAR", SEL, 1)
with iff("IS_NUMBER_GREATER_THAN_INT_LVAR 0 %s" % SEL):
    e("SET_LVAR_INT", SEL, 0)
e("GOSUB @PREVIEW_SHOT")
e("RETURN")

# camera jumps to the selected shot
lab("PREVIEW_SHOT")
with iff(eq(CNT, 0)):
    e("RETURN")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
e("GOSUB @LOAD_SHOT")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
e("RETURN")

# --------------------------------------------------------------- playback
# Every shot lasts its duration. The next shot either flies in smoothly
# (camera moves during the current shot's time) or is a hard cut.
lab("PLAY_SCENE")
with iff(eq(CNT, 0)):
    e("RETURN")
e("SET_LVAR_INT", EXC, 0)
e("SET_LVAR_INT", HID, 1)
e("SET_LVAR_INT", PI, 0)
e("SET_LVAR_INT", IDX, 0)
e("GOSUB @LOAD_SHOT")
e("CAMERA_RESET_NEW_SCRIPTABLES")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
e("SET_LVAR_INT", TMP, 800)
e("GOSUB @PLAY_WAIT")
with iff(eq(T, 99)):
    e("GOTO @PL_END")
lab("PL_LOOP")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, PI)
e("GOSUB @GET_SHOT_DUR")
e("SET_LVAR_INT_TO_LVAR_INT", TMP, OUT)
e("SET_LVAR_INT_TO_LVAR_INT", IDX, PI)
e("ADD_VAL_TO_INT_LVAR", IDX, 1)
with iff("IS_INT_LVAR_GREATER_THAN_INT_LVAR %s %s" % (CNT, IDX)):
    e("GOSUB @GET_SHOT_TYPE")
    with iff(eq(OUT, 0)):
        e("GOTO @PL_SMOOTH")
# hold the current shot, then cut to the next one
e("GOSUB @PLAY_WAIT")
with iff(eq(T, 99)):
    e("GOTO @PL_END")
e("ADD_VAL_TO_INT_LVAR", PI, 1)
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_INT_LVAR %s %s" % (PI, CNT)):
    e("GOTO @PL_END")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, PI)
e("GOSUB @LOAD_SHOT")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
e("GOTO @PL_LOOP")

lab("PL_SMOOTH")
# remember target, position and fov of the current shot (scratch memory)
e("GOSUB @CALC_TARGET")
e("SET_LVAR_INT_TO_LVAR_INT", A, MEM)
e("ADD_VAL_TO_INT_LVAR", A, SCRATCH)
for v in (F0, F1, F2, CX, CY, CZ, FOV):
    e("WRITE_MEMORY", A, v, 4, 0, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
e("SET_LVAR_INT_TO_LVAR_INT", IDX, PI)
e("ADD_VAL_TO_INT_LVAR", IDX, 1)
e("GOSUB @LOAD_SHOT")
e("GOSUB @CALC_TARGET")
e("SET_LVAR_INT_TO_LVAR_INT", A, MEM)
e("ADD_VAL_TO_INT_LVAR", A, SCRATCH)
for v in (F3, ZN, OUT):
    e("READ_MEMORY", v, A, 4, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
e("CAMERA_RESET_NEW_SCRIPTABLES")
e("CAMERA_PERSIST_POS 1")
e("CAMERA_PERSIST_TRACK 1")
e("CAMERA_PERSIST_FOV 1")
e("CAMERA_SET_VECTOR_TRACK", F3, ZN, OUT, F0, F1, F2, TMP, 1)
for v in (F0, F1, F2, F3):
    e("READ_MEMORY", v, A, 4, 0)
    e("ADD_VAL_TO_INT_LVAR", A, 4)
e("CAMERA_SET_VECTOR_MOVE", F0, F1, F2, CX, CY, CZ, TMP, 1)
e("CAMERA_SET_LERP_FOV", F3, FOV, TMP, 1)
e("GOSUB @PLAY_WAIT")
e("CAMERA_RESET_NEW_SCRIPTABLES")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
with iff(eq(T, 99)):
    e("GOTO @PL_END")
e("ADD_VAL_TO_INT_LVAR", PI, 1)
e("GOTO @PL_LOOP")

lab("PL_END")
e("CAMERA_RESET_NEW_SCRIPTABLES")
e("GOSUB @APPLY_CAM")
e("GOSUB @APPLY_FOV")
e("SET_LVAR_INT", HID, 0)
e("SET_LVAR_INT", ZN, 0)
e("RETURN")

# waits TMP ms; a touch anywhere stops the scene (T = 99)
lab("PLAY_WAIT")
e("SET_LVAR_INT", TA, 0)
lab("PW_LOOP")
e("WAIT 0")
e("GOSUB @GET_PRESSED")
with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 0" % ZN):
    e("GOSUB @WAIT_RELEASE")
    e("SET_LVAR_INT", T, 99)
    e("RETURN")
with iff("IS_INT_LVAR_GREATER_THAN_INT_LVAR %s %s" % (TA, TMP)):
    e("SET_LVAR_INT", T, 0)
    e("RETURN")
e("GOTO @PW_LOOP")

# ---------------------------------------------------------------- actors
# A = address of actor slot IDX (0..5)
lab("ACT_PTR")
e("SET_LVAR_INT_TO_LVAR_INT", A, IDX)
e("MULT_INT_LVAR_BY_VAL", A, 4)
e("ADD_INT_LVAR_TO_INT_LVAR", A, MEM)
e("ADD_VAL_TO_INT_LVAR", A, ACTORS_OFF)
e("RETURN")

# T = handle of the selected character or -1
lab("GET_SEL")
with iff(eq(SCH, 0)):
    e("SET_LVAR_INT_TO_LVAR_INT", T, PLR)
    e("RETURN")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, SCH)
e("SUB_VAL_FROM_INT_LVAR", IDX, 1)
e("GOSUB @ACT_PTR")
e("READ_MEMORY", T, A, 4, 0)
with iff("NOT IS_INT_LVAR_EQUAL_TO_NUMBER %s -1" % T):
    with iff("DOES_CHAR_EXIST %s" % T):
        e("RETURN")
e("WRITE_MEMORY", A, -1, 4, 0, 0)
e("SET_LVAR_INT", SCH, 0)
e("SET_LVAR_INT", T, -1)
e("RETURN")

lab("SPAWN_ACTOR")
e("GOSUB @POINT_AHEAD")
e("SET_LVAR_INT", IDX, 0)
lab("SP_FIND")
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s %d" % (IDX, MAX_ACTORS)):
    e("RETURN")
e("GOSUB @ACT_PTR")
e("READ_MEMORY", T, A, 4, 0)
with iff(eq(T, -1)):
    e("GOTO @SP_FREE")
with iff("NOT DOES_CHAR_EXIST %s" % T):
    e("GOTO @SP_FREE")
e("ADD_VAL_TO_INT_LVAR", IDX, 1)
e("GOTO @SP_FIND")
lab("SP_FREE")
with iff(eq(MOD, 0)):
    e("CREATE_RANDOM_CHAR", F0, F1, F2, T)
    e("GOTO @SP_MADE")
for i, m in enumerate(MODELS[1:], 1):
    with iff(eq(MOD, i)):
        e("SET_LVAR_INT", OUT, m[0])
e("REQUEST_MODEL", OUT)
e("SET_LVAR_INT", TMP, 0)
lab("SP_LOAD")
with iff("HAS_MODEL_LOADED %s" % OUT):
    e("GOTO @SP_CREATE")
e("WAIT 0")
e("ADD_VAL_TO_INT_LVAR", TMP, 1)
with iff("IS_INT_LVAR_GREATER_THAN_NUMBER %s 300" % TMP):
    e("RETURN")
e("GOTO @SP_LOAD")
lab("SP_CREATE")
e("CREATE_CHAR", 4, OUT, F0, F1, F2, T)
e("MARK_MODEL_AS_NO_LONGER_NEEDED", OUT)
lab("SP_MADE")
with iff("DOES_CHAR_EXIST %s" % T):
    e("WRITE_MEMORY", A, T, 4, 0, 0)
    e("SET_LVAR_INT_TO_LVAR_INT", SCH, IDX)
    e("ADD_VAL_TO_INT_LVAR", SCH, 1)
    e("SET_LVAR_FLOAT_TO_LVAR_FLOAT", F3, HD)
    e("ADD_VAL_TO_FLOAT_LVAR", F3, "180.0")
    e("SET_CHAR_HEADING", T, F3)
e("RETURN")

lab("DELETE_ACTOR")
with iff(eq(SCH, 0)):
    e("RETURN")
e("GOSUB @GET_SEL")
with iff("NOT IS_INT_LVAR_EQUAL_TO_NUMBER %s -1" % T):
    e("DELETE_CHAR", T)
    e("WRITE_MEMORY", A, -1, 4, 0, 0)
e("SET_LVAR_INT", SCH, 0)
e("RETURN")

# CJ -> actor 1 -> ... -> actor 6 -> CJ, skipping empty slots
lab("SELECT_NEXT")
e("SET_LVAR_INT_TO_LVAR_INT", IDX, SCH)
lab("SN_LOOP")
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s %d" % (IDX, MAX_ACTORS)):
    e("SET_LVAR_INT", SCH, 0)
    e("RETURN")
e("GOSUB @ACT_PTR")
e("READ_MEMORY", T, A, 4, 0)
e("ADD_VAL_TO_INT_LVAR", IDX, 1)
with iff("NOT IS_INT_LVAR_EQUAL_TO_NUMBER %s -1" % T):
    with iff("DOES_CHAR_EXIST %s" % T):
        e("SET_LVAR_INT_TO_LVAR_INT", SCH, IDX)
        e("RETURN")
e("GOTO @SN_LOOP")

# selected char and its partner (CJ <-> first actor) turn to each other
lab("FACE_EACH_OTHER")
e("GOSUB @GET_SEL")
with iff(eq(T, -1)):
    e("RETURN")
e("SET_LVAR_INT_TO_LVAR_INT", OUT, PLR)
with iff(eq(SCH, 0)):
    e("SET_LVAR_INT", IDX, 0)
    lab("FE_LOOP")
    with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s %d" % (IDX, MAX_ACTORS)):
        e("RETURN")
    e("GOSUB @ACT_PTR")
    e("READ_MEMORY", OUT, A, 4, 0)
    e("ADD_VAL_TO_INT_LVAR", IDX, 1)
    with iff(eq(OUT, -1)):
        e("GOTO @FE_LOOP")
    with iff("NOT DOES_CHAR_EXIST %s" % OUT):
        e("GOTO @FE_LOOP")
e("TASK_TURN_CHAR_TO_FACE_CHAR", T, OUT)
e("TASK_TURN_CHAR_TO_FACE_CHAR", OUT, T)
e("RETURN")

# animation ANI on character T
lab("PLAY_ANIM")
with iff(eq(T, -1)):
    e("RETURN")
for ifp in ("GANGS", "ON_LOOKERS", "DANCING"):
    idxs = [i for i, a in enumerate(ANIMS) if a[1] == ifp]
    conds = [eq(ANI, i) for i in idxs]
    q = ("'%s'" if len(ifp) <= 7 else '"%s"') % ifp
    with iff(*conds, any_of=True):
        with iff("NOT HAS_ANIMATION_LOADED %s" % q):
            e("REQUEST_ANIMATION", q)
            e("RETURN")
for i, (name, ifp, loop, keep, _, _) in enumerate(ANIMS):
    q = ("'%s'" if len(ifp) <= 7 else '"%s"') % ifp
    n = ("'%s'" if len(name) <= 7 else '"%s"') % name
    with iff(eq(ANI, i)):
        e("TASK_PLAY_ANIM", T, n, q, "4.0", loop, 0, 0, keep, -1)
        e("RETURN")
e("RETURN")

# ----------------------------------------------------------------- world
# FLG bits: 1 widescreen bars, 2 empty streets, 4 CJ hidden
lab("FLAG_BITS")   # -> TMP bars, OUT empty, IDX hidden
e("SET_LVAR_INT_TO_LVAR_INT", A, FLG)
e("SET_LVAR_INT", IDX, 0)
e("SET_LVAR_INT", OUT, 0)
e("SET_LVAR_INT", TMP, 0)
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s 4" % A):
    e("SET_LVAR_INT", IDX, 1)
    e("SUB_VAL_FROM_INT_LVAR", A, 4)
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s 2" % A):
    e("SET_LVAR_INT", OUT, 1)
    e("SUB_VAL_FROM_INT_LVAR", A, 2)
e("SET_LVAR_INT_TO_LVAR_INT", TMP, A)
e("RETURN")

lab("TOGGLE_WIDE")
e("GOSUB @FLAG_BITS")
ifelse([eq(TMP, 1)],
       lambda: (e("SUB_VAL_FROM_INT_LVAR", FLG, 1), e("SWITCH_WIDESCREEN 0")),
       lambda: (e("ADD_VAL_TO_INT_LVAR", FLG, 1), e("SWITCH_WIDESCREEN 1")))
e("RETURN")

lab("TOGGLE_EMPTY")
e("GOSUB @FLAG_BITS")
ifelse([eq(OUT, 1)],
       lambda: (e("SUB_VAL_FROM_INT_LVAR", FLG, 2), e("SET_PED_DENSITY_MULTIPLIER 1.0"),
                e("SET_CAR_DENSITY_MULTIPLIER 1.0")),
       lambda: (e("ADD_VAL_TO_INT_LVAR", FLG, 2), e("SET_PED_DENSITY_MULTIPLIER 0.0"),
                e("SET_CAR_DENSITY_MULTIPLIER 0.0"), e("CLEAR_AREA", CX, CY, CZ, "150.0", 1)))
e("RETURN")

lab("TOGGLE_HIDE")
e("GOSUB @FLAG_BITS")
with iff(eq(IDX, 1)):
    e("SUB_VAL_FROM_INT_LVAR", FLG, 4)
    e("GOSUB @SHOW_CJ")
    e("RETURN")
e("ADD_VAL_TO_INT_LVAR", FLG, 4)
e("SET_CHAR_VISIBLE", PLR, 0)
with iff("NOT IS_CHAR_IN_ANY_CAR %s" % PLR):
    e("FREEZE_CHAR_POSITION", PLR, 1)
e("RETURN")

# CJ becomes visible again, standing on the ground under the camera
lab("SHOW_CJ")
e("SET_CHAR_VISIBLE", PLR, 1)
with iff("NOT IS_CHAR_IN_ANY_CAR %s" % PLR):
    e("GET_GROUND_Z_FOR_3D_COORD", CX, CY, CZ, F3)
    e("SET_CHAR_COORDINATES", PLR, CX, CY, F3)
    e("FREEZE_CHAR_POSITION", PLR, 0)
e("RETURN")

# hidden CJ travels with the camera so the city loads around it
lab("FOLLOW")
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s 4" % FLG):
    with iff("NOT IS_CHAR_IN_ANY_CAR %s" % PLR):
        e("SET_CHAR_COORDINATES", PLR, CX, CY, CZ)
e("RETURN")

# ------------------------------------------------------------------- UI
lab("DRAW_UI")
with iff(eq(HID, 1)):
    e("RETURN")
for p in range(7):
    with iff(eq(PAGE, p)):
        e("GOTO @UI_%d" % p)
e("RETURN")


def status_num(key, *nums, line=0):
    status_style()
    cmd = {0: "DISPLAY_TEXT", 1: "DISPLAY_TEXT_WITH_NUMBER", 2: "DISPLAY_TEXT_WITH_2_NUMBERS"}[len(nums)]
    e(cmd, "320.0", fl(STATUS_Y[line]), "'%s'" % key, *nums)


def shots_status():
    def none():
        status_num("DS_NONE")

    def some():
        e("SET_LVAR_INT_TO_LVAR_INT", TMP, SEL)
        e("ADD_VAL_TO_INT_LVAR", TMP, 1)
        status_num("DS_NUM", TMP, CNT)
        e("SET_LVAR_INT_TO_LVAR_INT", IDX, SEL)
        e("GOSUB @GET_SHOT_DUR")
        e("SET_LVAR_INT_TO_LVAR_INT", TMP, OUT)
        e("DIV_INT_LVAR_BY_VAL", TMP, 1000)
        e("SET_LVAR_INT_TO_LVAR_INT", A, TMP)
        e("MULT_INT_LVAR_BY_VAL", A, 1000)
        e("SUB_INT_LVAR_FROM_INT_LVAR", OUT, A)
        e("DIV_INT_LVAR_BY_VAL", OUT, 100)
        e("SET_LVAR_INT_TO_LVAR_INT", T, OUT)
        e("GOSUB @GET_SHOT_TYPE")
        ifelse([eq(OUT, 0)], lambda: status_num("DS_SM", TMP, T, line=1),
               lambda: status_num("DS_CT", TMP, T, line=1))
    ifelse([eq(CNT, 0)], none, some)


# main
lab("UI_0")
button(4, "DB_HIDE")
button(1, "DB_CAM")
button(2, "DB_SHT")
button(3, "DB_ACT")
button(7, "DB_WLD")
button(8, "DB_PLAY")
button(9, "DB_ADD")
ifelse([eq(EXC, 1)], lambda: button(6, "DB_SURE"), lambda: button(6, "DB_EXIT"))
status_num("DS_CNT", CNT, line=1)
e("RETURN")

# camera (faint buttons so the picture stays visible)
lab("UI_1")
for z, k in ((4, "DC_FWD"), (6, "DC_BCK"), (2, "DC_TL"), (8, "DC_TR"), (1, "DC_UP"),
             (3, "DC_DN"), (7, "DC_PU"), (9, "DC_PD"), (5, "DB_MENU")):
    button(z, k, faint=True)
e("RETURN")

lab("UI_2")
for z, k in ((4, "DB_BACK"), (1, "DS_ADD"), (2, "DS_CUT"), (3, "DS_DEL"), (7, "DS_PRV"),
             (8, "DS_NXT"), (9, "DB_MORE"), (6, "DB_CAM")):
    button(z, k)
shots_status()
e("RETURN")

lab("UI_3")
for z, k in ((4, "DB_BACK"), (1, "DS_TP"), (2, "DS_TM"), (3, "DS_TYP"), (7, "DS_ZI"),
             (8, "DS_ZO"), (9, "DS_UPD")):
    button(z, k)
ifelse([eq(EXC, 2)], lambda: button(6, "DB_SURE"), lambda: button(6, "DS_CLR"))
shots_status()
e("RETURN")


def actor_status():
    ifelse([eq(SCH, 0)], lambda: status_num("DA_CJ"), lambda: status_num("DA_NUM", SCH))
    for i in range(len(MODELS)):
        with iff(eq(MOD, i)):
            status_num("DM%d" % i, line=1)
    with iff(eq(ANI, -1)):
        status_num("DA_NOAN", line=2)
    for i in range(len(ANIMS)):
        with iff(eq(ANI, i)):
            status_num("DN%d" % i, line=2)


lab("UI_4")
for z, k in ((4, "DB_BACK"), (1, "DA_ADD"), (2, "DA_MOD"), (3, "DA_DEL"), (7, "DA_SEL"),
             (8, "DA_ANX"), (6, "DA_ANP"), (9, "DB_MORE")):
    button(z, k)
actor_status()
e("RETURN")

lab("UI_5")
for z, k in ((4, "DB_BACK"), (1, "DA_WLK"), (2, "DA_RUN"), (3, "DA_STP"), (7, "DA_FCE"),
             (8, "DA_LKC"), (9, "DA_SEL")):
    button(z, k)
actor_status()
e("RETURN")

lab("UI_6")
e("GOSUB @FLAG_BITS")
for z, k in ((4, "DB_BACK"), (1, "DW_HP"), (2, "DW_HM"), (3, "DW_WTH"), (7, "DW_SLO")):
    button(z, k)
ifelse([eq(TMP, 1)], lambda: button(8, "DW_BR1"), lambda: button(8, "DW_BR0"))
ifelse([eq(OUT, 1)], lambda: button(9, "DW_EM1"), lambda: button(9, "DW_EM0"))
ifelse([eq(IDX, 1)], lambda: button(6, "DW_CJ1"), lambda: button(6, "DW_CJ0"))
e("GET_TIME_OF_DAY", TMP, OUT)
status_num("DW_TIM", TMP, WTH)
for i in range(3):
    with iff(eq(SLO, i)):
        status_num("DW_S%d" % i, line=1)
e("RETURN")

# ------------------------------------------------------------------ exit
lab("EXIT")
e("SET_LVAR_INT", HID, 1)
e("SET_LVAR_INT", ZN, 6)
e("GOSUB @WAIT_RELEASE")
e("CAMERA_RESET_NEW_SCRIPTABLES")
with iff("IS_INT_LVAR_GREATER_OR_EQUAL_TO_NUMBER %s 4" % FLG):
    e("GOSUB @SHOW_CJ")
e("SET_CHAR_VISIBLE", PLR, 1)
e("SWITCH_WIDESCREEN 0")
e("SET_PED_DENSITY_MULTIPLIER 1.0")
e("SET_CAR_DENSITY_MULTIPLIER 1.0")
e("SET_TIME_SCALE 1.0")
e("RELEASE_WEATHER")
e("SET_LVAR_INT", IDX, 0)
lab("EX_ACTORS")
e("GOSUB @ACT_PTR")
e("READ_MEMORY", T, A, 4, 0)
with iff("NOT IS_INT_LVAR_EQUAL_TO_NUMBER %s -1" % T):
    with iff("DOES_CHAR_EXIST %s" % T):
        e("MARK_CHAR_AS_NO_LONGER_NEEDED", T)
e("ADD_VAL_TO_INT_LVAR", IDX, 1)
with iff("IS_NUMBER_GREATER_THAN_INT_LVAR %d %s" % (MAX_ACTORS, IDX)):
    e("GOTO @EX_ACTORS")
e("FREE_MEMORY", MEM)
e("CLEAR_CHAR_TASKS", PLR)
e("RESTORE_CAMERA_JUMPCUT")
e("SET_CAMERA_BEHIND_PLAYER")
e("DISPLAY_HUD 1")
e("DISPLAY_RADAR 1")
e("USE_TEXT_COMMANDS 0")
e("SET_CHAR_PROOFS", PLR, "0 0 0 0 0")
e("SET_EVERYONE_IGNORE_PLAYER 0 0")
e("SET_PLAYER_CONTROL 0 1")
e("#ifdef CSA")
e("GOTO @ACTIVATE")
e("#else")
e("TERMINATE_THIS_SCRIPT")
e("#endif")

print("\n".join(out))
