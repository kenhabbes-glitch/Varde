import html, re, collections
E_ = html.escape
ORDER = ['U', 'Q', 'D', 'L', 'FB', 'K', 'C', 'R', 'Y', 'F', 'S', 'BT', 'J', 'AE']

def refkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r)
    if not m: return (99, r)
    p, n = m.group(1), int(m.group(2))
    return (ORDER.index(p) if p in ORDER else 50, p, n)

def groups(B):
    g = collections.OrderedDict()
    for ref, val, desc in B.bom:
        if ref.startswith('(') or ref.endswith('B') and ref[:-1].startswith('U') and 'samme' in desc: continue
        r = ref[:-1] if re.match(r'U\d+A$', ref) else ref
        key = (re.match(r'[A-Z]+', r).group(0), val, desc)
        g.setdefault(key, []).append(r)
    rows = []
    for (p, val, desc), refs in g.items():
        refs = sorted(set(refs), key=refkey)
        qty = len(refs)
        mm = re.search(r'(\d+) × ', val) or re.search(r'(\d+) stk', desc)
        if mm and p in ('C', 'R'): qty *= int(mm.group(1))
        rows.append((refs, qty, val, desc))
    rows.sort(key=lambda r: refkey(r[0][0]))
    return rows

def legend_svg():
    from lib import Board, Sheet
    b = Board('X', 'x'); s = Sheet(b, 'x')
    s.label((20, 8), 'NETTNAVN', 'r', 6); s.text(52, 8.7, 'Nett med navn. Samme navn = koplet, også på andre ark.', 2.2)
    s.pwr((24, 22), '3V3_AON', 'u'); s.text(52, 20.7, 'Forsyningsnett.', 2.2)
    s.gnd((24, 30)); s.text(52, 32.7, 'Jord (GND). GND_ISO er isolert jord på CAN-siden.', 2.2)
    s.wire((18, 42), (30, 42)); s.dot((24, 42)); s.wire((24, 42), (24, 46)); s.text(52, 42.7, 'Prikk = kopling. Kryss uten prikk = ingen kopling.', 2.2)
    s.line(23.1, 53.1, 24.9, 54.9, 0.3); s.line(23.1, 54.9, 24.9, 53.1, 0.3); s.wire((18, 54), (24, 54)); s.text(52, 54.7, 'Pinne ikke koplet (NC).', 2.2)
    s.text(20, 66.7, '127 kΩ*', 2.2, 'start', '#5b5b57'); s.text(52, 66.7, 'Stjerne = verdien beregnes eller avstemmes ved design og test.', 2.2)
    s.text(20, 76.7, 'DNP', 2.2, 'start', '#5b5b57'); s.text(52, 76.7, 'Ikke montert som standard (plass for tilpasning).', 2.2)
    body = '\n'.join(s.o)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="14 0 130 82" width="175mm" height="110mm" font-family="Helvetica, Arial, sans-serif">{body}</svg>'

def cover(bs, date, pages_before):
    rows = []; page = pages_before + 1
    for B in bs:
        for i, sh in enumerate(B.sheets):
            rows.append(f'<tr><td>{E_(B.code)}</td><td>{E_(B.name)}</td><td>{i+1}</td><td>{E_(sh.title)}</td><td class="n">{page}</td></tr>'); page += 1
    bom_start = page
    rows.append(f'<tr class="bom"><td>Alle</td><td>Alle kort</td><td>–</td><td>Stykklister generert fra skjemaene</td><td class="n">{page}–</td></tr>')
    return f'''<div class="pg cover"><div class="frame">
<div class="hdr"><div class="kick">GPS Vs Tyv</div><h1>Elektriske skjemaer for alle kretskort</h1>
<p class="sub">Revisjon 0.1 · {E_(date)} · Grunnlag for anbud til maskinvareleverandør</p></div>
<div class="cols"><div>
<h2>Innhold</h2><table class="idx"><thead><tr><th>Kort</th><th>Navn</th><th>Ark</th><th>Innhold</th><th class="n">Side</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</div><div>
<div class="warn"><b>Status: utkast.</b> Skjemaene viser valgt arkitektur, komponenter, grensesnitt og nettnavn på pinnenivå. De er ikke kontrollert mot alle datablad og ikke simulert. Pinnenummer settes når symbolene hentes fra produsentenes biblioteker i leverandørens CAD-verktøy (KiCad eller Altium). Verdier merket * beregnes ved design.</div>
<h2>Tegnforklaring</h2>{legend_svg()}
<h2>Generelle regler</h2><ul>
<li>Hvert kort har egne referanser (U1, R1 …). Kortkoden står i tittelfeltet: HE hovedenhet, KP kamerapod, UB utvidelsesboks, SN sensornode, BS og BL utstyrsbrikker.</li>
<li>Avkopling: 100 nF ved hver forsyningspinne og bulk etter datablad, også der det bare står i merknad.</li>
<li>ESD- og overspenningsvern på alle signaler som går ut av kapslingen.</li>
<li>RF: 50 Ω coplanar med jordvias, tilpasningsnett ved hver antenne, ingen kobber under antenner.</li>
<li>Sikkerhet: SWD låses i produksjon. Nøkler genereres i sikkerhetsbrikkene og forlater dem aldri.</li>
<li>Kamerahub = utvidelsesboks uten EOL-innganger og reléer, med to porter. Stasjonær enhet (brakke/container) = hovedenhet + utvidelsesboks.</li>
<li>Referansedesign fra Nordic, Himax, Acconeer, u-blox og TI følges for detaljer som ikke er tegnet.</li></ul>
</div></div></div></div>'''

def bom(bs):
    out = []
    for B in bs:
        rows = ''.join(f'<tr><td class="refs">{E_(", ".join(r))}</td><td class="n">{q}</td><td>{E_(v)}</td><td>{E_(d)}</td></tr>' for r, q, v, d in groups(B))
        out.append(f'<section class="bomsec"><h2>Stykkliste: {E_(B.code)} {E_(B.name)}</h2><p class="sub">Generert fra skjemaet, rev. 0.1. Passive komponenter: 0402/0603, X7R/X5R der ikke annet er angitt. Endelig liste med produsentnummer lages av leverandør.</p><table class="bomt"><thead><tr><th>Referanser</th><th class="n">Antall</th><th>Verdi / type</th><th>Beskrivelse</th></tr></thead><tbody>{rows}</tbody></table></section>')
    return ''.join(out)

CSS = '''
@page{size:420mm 297mm;margin:0}
@page bom{size:420mm 297mm;margin:14mm 16mm}
body{margin:0;font-family:Helvetica,Arial,sans-serif;color:#1a1a1a}
.pg{width:420mm;height:297mm;page-break-after:always;overflow:hidden;position:relative}
svg{display:block}
.cover .frame{position:absolute;inset:8mm;border:0.5mm solid #1a1a1a;padding:12mm 14mm}
.kick{font-size:11pt;letter-spacing:.08em;text-transform:uppercase;color:#6b6a66}
h1{font-size:28pt;margin:2mm 0 2mm}
.sub{color:#5b5b57;font-size:10pt;margin:0 0 6mm}
.cols{display:grid;grid-template-columns:1.15fr 1fr;gap:12mm}
h2{font-size:12pt;margin:6mm 0 3mm}
table{border-collapse:collapse;width:100%;font-size:8.6pt}
th{text-align:left;border-bottom:0.4mm solid #1a1a1a;padding:1.4mm 2mm;font-weight:bold}
td{border-bottom:0.2mm solid #ddd;padding:1.2mm 2mm;vertical-align:top}
td.n,th.n{text-align:right}
tr.bom td{color:#5b5b57}
.warn{background:#fff6e0;border:0.3mm solid #e0b24a;border-radius:1.5mm;padding:3mm 4mm;font-size:9.5pt;line-height:1.4}
ul{font-size:9.2pt;line-height:1.45;padding-left:5mm}
.bomsec{page:bom;page-break-before:always}
.bomt{font-size:8.4pt}
.bomt td.refs{width:34%;color:#0b4f9c}
.bomt thead{display:table-header-group}
.bomt tr{page-break-inside:avoid}
'''
