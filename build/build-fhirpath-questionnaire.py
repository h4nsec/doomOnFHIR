"""Generate the pure-FHIRPath Doom Questionnaire.

All game logic lives in SDC `variable` / `calculatedExpression` extensions.
The player's input is a single string item; every character is one command,
so the response's input history *is* the game state (replayed with aggregate()).
"""
import json, re, sys

W = 16
MAP = [
    "################",
    "#......#.....I.#",
    "#.####.#.###...#",
    "#.#I...#...#.#.#",
    "#.#.####.#.#.#.#",
    "#...+....#...#.#",
    "###.######.###.#",
    "#......I.#.....#",
    "#.######.#.###.#",
    "#.#....#.#.#X#.#",
    "#.#.##.#...#.#.#",
    "#...#I.#####.#.#",
    "###.#.##.....#.#",
    "#+..#....###.I.#",
    "#.#...##.......#",
    "################",
]
assert all(len(r) == W for r in MAP) and len(MAP) == W
START = (1, 14, 0)  # x, y, facing (0=N 1=E 2=S 3=W)
CW, CH = 48, 16      # screen size in braille chars
PW, PH = CW * 2, CH * 4  # ... and in pixels
TSTEP, TMAX = 0.1, 12.0
NSTEPS = int(TMAX / TSTEP)

def fp(s):
    """Collapse whitespace so expressions stay readable here but compact in JSON."""
    parts = s.split("'")  # even = code, odd = inside a string literal (no escaped quotes used)
    return "'".join(re.sub(r"\s+", " ", p) if i % 2 == 0 else p for i, p in enumerate(parts)).strip()

def eff(i, cl="%cleared"):
    """Effective map cell at index expression i (cleared imps / used medkits read as floor)."""
    return f"iif({cl}.contains('|' & ({i}).toString() & '|'), '.', %map.substring({i}, 1))"

# ---------------------------------------------------------------- game step
# $this = one command char, $total = state "x,y,d,hp,kills,status,cleared,msg"
STEP = fp(f"""
defineVariable('c', $this)
.defineVariable('s', $total.split(','))
.defineVariable('x', %s[0].toInteger())
.defineVariable('y', %s[1].toInteger())
.defineVariable('d', %s[2].toInteger())
.defineVariable('hp', %s[3].toInteger())
.defineVariable('k', %s[4].toInteger())
.defineVariable('st', %s[5])
.defineVariable('cl', %s[6])
.defineVariable('dx', iif(%d = 1, 1, iif(%d = 3, -1, 0)))
.defineVariable('dy', iif(%d = 2, 1, iif(%d = 0, -1, 0)))
.defineVariable('m', iif(%c = 'w', 1, iif(%c = 's', -1, 0)))
.defineVariable('ti', (%y + %dy * %m) * %W + %x + %dx * %m)
.defineVariable('tc', {eff('%ti', '%cl')})
.defineVariable('mv', %m != 0 and %tc != '#' and %tc != 'I')
.defineVariable('nx', iif(%mv, %x + %dx * %m, %x))
.defineVariable('ny', iif(%mv, %y + %dy * %m, %y))
.defineVariable('nd', iif(%c = 'a', (%d + 3) mod 4, iif(%c = 'd', (%d + 1) mod 4, %d)))
.defineVariable('hit', iif(%c = 'f',
    %range8.select((%y + %dy * $this) * %W + %x + %dx * $this)
           .where({eff('$this', '%cl')} != '.' and {eff('$this', '%cl')} != '+').first(), {{}}))
.defineVariable('kill', iif(%hit.exists(), %map.substring(%hit, 1) = 'I', false))
.defineVariable('pick', %mv and %tc = '+')
.defineVariable('ncl', %cl & iif(%kill, %hit.toString() & '|', '') & iif(%pick, %ti.toString() & '|', ''))
.defineVariable('hp1', iif(%pick, iif(%hp + 25 > 100, 100, %hp + 25), %hp))
.defineVariable('near', %imps.where(%ncl.contains('|' & $this.toString() & '|').not()
    and defineVariable('ix', $this mod %W).defineVariable('iy', $this div %W)
        .defineVariable('sx', iif(%ix > %nx, 1, iif(%ix < %nx, -1, 0)))
        .defineVariable('sy', iif(%iy > %ny, 1, iif(%iy < %ny, -1, 0)))
        .defineVariable('dist', (%ix - %nx).abs() + (%iy - %ny).abs())
        .select((%ix = %nx or %iy = %ny) and %dist <= 4
            and %range8.where($this < %dist)
                .where({eff('(%ny + %sy * $this) * %W + %nx + %sx * $this', '%ncl')} = '#').empty())
    ).count())
.defineVariable('hp2', %hp1 - 8 * %near)
.defineVariable('nst', iif(%hp2 <= 0, 'dead', iif(%mv and %tc = 'X', 'won', 'play')))
.defineVariable('msg', (iif(%kill, 'IMP DOWN!', iif(%c = 'f', '*BLAM* (missed)',
    iif(%pick, 'Picked up a medikit (+25)', iif(%m != 0 and %mv.not(), 'Blocked.', ''))))
    & iif(%near > 0, ' Imp fireball! -' & (8 * %near).toString() & ' HP', '')).trim())
.select(iif(%st != 'play', $total,
    %nx.toString() & ',' & %ny.toString() & ',' & %nd.toString() & ',' & iif(%hp2 < 0, 0, %hp2).toString()
    & ',' & %nk_placeholder & ',' & %nst & ',' & %ncl & ',' & %msg))
""").replace("%nk_placeholder", "(%k + iif(%kill, 1, 0)).toString()")
# prefix step-local variable names with '_' so they never clash with Questionnaire-level variables
for n in "c s x y d hp k st cl dx dy m ti tc mv nx ny nd hit kill pick ncl hp1 near hp2 nst msg ix iy sx sy dist".split():
    STEP = re.sub(r"%" + n + r"\b", "%_" + n, STEP)
    STEP = STEP.replace("defineVariable('" + n + "'", "defineVariable('_" + n + "'")

# ---------------------------------------------------------------- renderer
# ---------------------------------------------------------------- braille renderer
# Each braille char (U+2800-U+28FF) is a 2x4 dot cell, and braille glyphs share one width even in
# proportional fonts (renderers like LHC-Forms force Arial), so the frame stays aligned anywhere.
BRAILLE = "".join(chr(0x2800 + i) for i in range(256))
DOT = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]  # DOT[row][col]

def braille_cells(bitmap):
    """bitmap: list of equal-length '0'/'1' strings, height multiple of 4, width multiple of 2."""
    rows = []
    for cy in range(0, len(bitmap), 4):
        line = ""
        for cx in range(0, len(bitmap[0]), 2):
            v = sum(DOT[r][c] for r in range(4) for c in range(2) if bitmap[cy + r][cx + c] == "1")
            line += BRAILLE[v]
        rows.append(line)
    return rows

# dither: band b in 0..4 (near..far), stored for x mod 4 as one PH-long column each
def lit_on(b, x, y):
    return [True,
            (x + y) % 4 != 0,
            (x + y) % 2 == 0,
            x % 2 == 0 and y % 2 == 0,
            x % 4 == 0 and y % 2 == 0][b]
DITH = "".join("".join("1" if lit_on(b, xm, y) else "0" for y in range(PH)) for b in range(5) for xm in range(4))
# floor, ordered horizon -> bottom, denser when closer; one per x mod 4
HALF = PH // 2
def floor_on(x, i):  # i = rows below horizon
    return [False, (x + i) % 8 == 0, (x + i) % 4 == 0, (x + i) % 2 == 0][min(3, i * 4 // HALF)]
FLOORPAT = "".join("".join("1" if floor_on(xm, i) else "0" for i in range(HALF)) for xm in range(4))
EXITPAT = "".join("1" if (y % 4) < 2 else "0" for y in range(PH))

IMP16 = [
    "1100000000000011",
    "1110000000000111",
    "0111111111111110",
    "0011111111111100",
    "0111111111111110",
    "0110001111000110",
    "0110000110000110",
    "0111111111111110",
    "0111111001111110",
    "0111110000111110",
    "0110000000000110",
    "0101010101010110",
    "0110000000000110",
    "0111111111111110",
    "0011111111111100",
    "0001111111111000",
]
IMPTEX = "".join(IMP16[r][c] for c in range(16) for r in range(16))  # column-major

SOLID = lambda xe, ye: (
    f"defineVariable('ci', ({ye}).floor() * %W + ({xe}).floor())"
    f".select({eff('%ci')} = '#' or {eff('%ci')} = 'I' or {eff('%ci')} = 'X')"
)
# one PH-long '0'/'1' pixel column per screen pixel column ($this = pixel column x)
COLUMN = fp(f"""
defineVariable('xm', $this mod 4)
.defineVariable('cam', 2.0 * $this / %PW - 1)
.defineVariable('rx', %dx + %plx * %cam)
.defineVariable('ry', %dy + %ply * %cam)
.defineVariable('t', %tsteps.where({SOLID('%px + %rx * $this', '%py + %ry * $this')}).first())
.defineVariable('tt', iif(%t.exists(), %t, %TMAX))
.defineVariable('hi', (%py + %ry * %tt).floor() * %W + (%px + %rx * %tt).floor())
.defineVariable('hc', iif(%t.exists(), %map.substring(%hi, 1), ' '))
.defineVariable('side', (%px + %rx * (%tt - %TSTEP)).floor() != (%px + %rx * %tt).floor())
.defineVariable('band', iif(%tt < 1.5, 0, iif(%tt < 3, 1, iif(%tt < 5, 2, 3))) + iif(%side, 1, 0))
.defineVariable('h', iif(%PH / %tt > %PH, %PH, (%PH / %tt).floor()))
.defineVariable('top', ((%PH - %h) / 2).floor())
.defineVariable('u', iif(%side, %py + %ry * %tt, %px + %rx * %tt))
.defineVariable('ui', ((%u - %u.floor()) * 16).floor())
.defineVariable('wall', iif(%t.exists().not(), %zeros.substring(0, %h),
    iif(%hc = 'I',
        %zeros.substring(0, %h).toChars().select(%imptex.substring(%ui * 16 + ($index * 16 / %h).floor(), 1)).join(''),
    iif(%hc = 'X', %exitpat.substring(%top, %h),
        %dith.substring((%band * 4 + %xm) * %PH + %top, %h)))))
.defineVariable('nf', %PH - %top - %h)
.select(%zeros.substring(0, %top) & %wall & %floorpat.substring(%xm * %HALF + %HALF - %nf, %nf))
""")

# pack pixel columns into braille: char (cx, cy) covers columns 2cx..2cx+1, rows 4cy..4cy+3
def bit(col, k):
    return f"%{col}.substring(%o + {k}, 1).toInteger()"
FRAME = fp(f"""
%crows.select(defineVariable('o', $this * 4).select(
  %ccols.select(defineVariable('a', %pix[2 * $this]).defineVariable('b', %pix[2 * $this + 1])
    .select(%braille.substring(
        {bit('a', 0)} + 2 * {bit('a', 1)} + 4 * {bit('a', 2)} + 64 * {bit('a', 3)}
      + 8 * {bit('b', 0)} + 16 * {bit('b', 1)} + 32 * {bit('b', 2)} + 128 * {bit('b', 3)}, 1))
  ).join(''))).join('\\n')
""")

# automap: each map cell is a 4x4-dot icon = 2 braille chars
ICONS4 = {
    "#": ["1111", "1111", "1111", "1111"],
    ".": ["0000", "0000", "0000", "0000"],
    "I": ["1001", "0110", "0110", "1001"],
    "+": ["0100", "1110", "0100", "0000"],
    "X": ["1111", "1001", "1001", "1111"],
}
ARROW4 = [  # N E S W
    ["0110", "1111", "0110", "0110"],
    ["0010", "1111", "1111", "0010"],
    ["0110", "0110", "1111", "0110"],
    ["0100", "1111", "1111", "0100"],
]
ICONSTR = "".join(braille_cells(ICONS4[k])[0] for k in "#.I+X")
ARROWSTR = "".join(braille_cells(a)[0] for a in ARROW4)
DIRS = "'NESW'"
MINIMAP = fp(f"""
%rows16.select(defineVariable('r', $this).select(
  %rows16.select(defineVariable('i', %r * %W + $this).select(
    iif(%i = %py0 * %W + %px0, %arrows.substring(%dir * 2, 2),
        %icons.substring('#.I+X'.indexOf({eff('%i')}) * 2, 2))
  )).join(''))).join('\\n')
""")

def lit(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

def var(name, expr):
    return {"url": "http://hl7.org/fhir/StructureDefinition/variable",
            "valueExpression": {"name": name, "language": "text/fhirpath", "expression": expr}}

def calc(expr):
    return {"url": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression",
            "valueExpression": {"language": "text/fhirpath", "expression": expr}}

init = f"{START[0]},{START[1]},{START[2]},100,0,play,|,You wake up in a hangar. Something growls."

variables = [
    var("map", lit("".join(MAP))),
    var("W", str(W)),
    var("PW", str(PW)),
    var("PH", str(PH)),
    var("HALF", str(HALF)),
    var("TSTEP", str(TSTEP)),
    var("TMAX", str(TMAX)),
    var("range8", "'12345678'.toChars().select($this.toInteger())"),
    var("rows16", "'" + "x" * W + "'.toChars().select($index)"),
    var("imps", "%map.toChars().select(iif($this = 'I', $index, {}))"),
    var("tsteps", f"'{'x' * NSTEPS}'.toChars().select(($index + 1) * {TSTEP})"),
    var("cols", "{}"),  # placeholder, replaced below (needs state vars first)
]
# input history -> state
variables = variables[:-1] + [
    var("input", "%resource.repeat(item).where(linkId = 'input').answer.value.first().lower()"),
    var("cmds", "iif(%input.exists(), %input.toChars().where('wasdf'.contains($this)), {})"),
    var("state", f"%cmds.aggregate({STEP}, {lit(init)}).split(',')"),
    var("px0", "%state[0].toInteger()"),
    var("py0", "%state[1].toInteger()"),
    var("dir", "%state[2].toInteger()"),
    var("hp", "%state[3].toInteger()"),
    var("kills", "%state[4].toInteger()"),
    var("status", "%state[5]"),
    var("cleared", "%state[6]"),
    var("msg", "%state[7]"),
    var("px", "%px0 + 0.5"),
    var("py", "%py0 + 0.5"),
    var("dx", "iif(%dir = 1, 1, iif(%dir = 3, -1, 0))"),
    var("dy", "iif(%dir = 2, 1, iif(%dir = 0, -1, 0))"),
    var("plx", "-0.66 * %dy"),
    var("ply", "0.66 * %dx"),
    var("zeros", lit("0" * PH)),
    var("dith", lit(DITH)),
    var("floorpat", lit(FLOORPAT)),
    var("exitpat", lit(EXITPAT)),
    var("imptex", lit(IMPTEX)),
    var("braille", lit(BRAILLE)),
    var("icons", lit(ICONSTR)),
    var("arrows", lit(ARROWSTR)),
    var("crows", f"'{'x' * CH}'.toChars().select($index)"),
    var("ccols", f"'{'x' * CW}'.toChars().select($index)"),
    var("pix", f"'{'x' * PW}'.toChars().select($index).select({COLUMN})"),
]

DEAD = "\n" * 6 + "Y O U   A R E   D E A D\n\nDelete some letters from the command box to undo time."
WON = "\n" * 6 + "L E V E L   C O M P L E T E\n\nPlease submit this questionnaire to your physician."

screen_expr = f"iif(%status = 'dead', {lit(DEAD)}, iif(%status = 'won', {lit(WON)}, {FRAME}))"
hud_expr = fp(f"""
'HEALTH ' & %hp.toString() & '%   KILLS ' & %kills.toString() & '/' & %imps.count().toString()
& '   FACING ' & {DIRS}.substring(%dir, 1) & '   MOVES ' & %cmds.count().toString()
& iif(%msg != '', '   ' & %msg, '')
""")

questionnaire = {
    "resourceType": "Questionnaire",
    "id": "doom-fhirpath",
    "meta": {"profile": ["http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-adapt"]},
    "url": "https://smartdoom.example/fhir/Questionnaire/doom-fhirpath",
    "version": "1.0.0",
    "name": "DoomFhirpath",
    "title": "Hangar Assessment (FHIRPath edition)",
    "status": "active",
    "subjectType": ["Patient"],
    "description": "A first-person shooter implemented entirely in FHIRPath. No JavaScript: the game "
                   "state is replayed from your input with aggregate() and every frame is ray-marched "
                   "by calculatedExpression. Works in any SDC renderer built on fhirpath.js >= 3.13 "
                   "(e.g. NLM LHC-Forms, CSIRO Smart Forms).",
    "extension": variables,
    "item": [
        {"linkId": "instructions", "type": "display",
         "text": "Type commands into the box below, one letter per action: W forward, S back, "
                 "A turn left, D turn right, F fire. Kill the imps (horned faces), grab medikits (+ on the automap) "
                 "and reach the exit (striped door, box on the automap). Imps hit you every turn while they can see you (same row or column, up to 4 squares). "
                 "Delete letters to undo time."},
        {"linkId": "screen", "type": "text", "readOnly": True, "text": "View",
         "extension": [calc(screen_expr)]},
        {"linkId": "hud", "type": "string", "readOnly": True, "text": "Status",
         "extension": [calc(hud_expr)]},
        {"linkId": "input", "type": "string", "text": "Commands (W/A/S/D/F)",
         "extension": [{"url": "http://hl7.org/fhir/StructureDefinition/entryFormat", "valueString": "wwdwwf..."}]},
        {"linkId": "minimap", "type": "text", "readOnly": True, "text": "Automap",
         "extension": [calc(MINIMAP)]},
        {"linkId": "outcome", "type": "group", "text": "Clinical outcome (auto-populated)", "item": [
            {"linkId": "outcome.health", "type": "integer", "readOnly": True, "text": "Health (%)",
             "extension": [calc("%hp")]},
            {"linkId": "outcome.kills", "type": "integer", "readOnly": True, "text": "Imps neutralised",
             "extension": [calc("%kills")]},
            {"linkId": "outcome.status", "type": "string", "readOnly": True, "text": "Disposition",
             "extension": [calc("iif(%status = 'won', 'Discharged (level complete)', "
                                "iif(%status = 'dead', 'Deceased', 'Still in the hangar'))")]},
        ]},
    ],
}

import os
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "doom-fhirpath-questionnaire.json")
with open(out, "w") as f:
    json.dump(questionnaire, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", out, len(json.dumps(questionnaire)), "bytes")
