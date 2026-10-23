#!/usr/bin/env python3
"""Genera el catálogo A–Z y la tabla periódica SVG de Azure Atlas.

Fuente única de verdad: data/servicios.csv
Salidas:
  - docs/17-catalogo-a-z.md
  - assets/azure-atlas-tabla-periodica.svg
  - assets/azure-atlas-banner.svg

Uso:  python3 tools/generar_atlas.py   (solo biblioteca estándar, Python 3.9+)
"""
from __future__ import annotations

import csv
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "data" / "servicios.csv"
CATALOGO = RAIZ / "docs" / "17-catalogo-a-z.md"
POSTER = RAIZ / "assets" / "azure-atlas-tabla-periodica.svg"
BANNER = RAIZ / "assets" / "azure-atlas-banner.svg"

EDICION = "octubre 2026"

# Familias en el orden del póster: (clave, nombre, color)
FAMILIAS = [
    ("computo", "Cómputo", "#60A5FA"),
    ("contenedores", "Contenedores", "#22D3EE"),
    ("almacenamiento", "Almacenamiento", "#A78BFA"),
    ("bases-de-datos", "Bases de datos", "#E879F9"),
    ("redes", "Redes", "#34D399"),
    ("integracion", "Integración", "#FB923C"),
    ("analitica", "Analítica", "#FACC15"),
    ("ia", "IA y ML", "#F472B6"),
    ("iot-hibrido", "IoT, borde e híbrido", "#A3E635"),
    ("identidad-seguridad", "Identidad y seguridad", "#F87171"),
    ("devops", "DevOps e IaC", "#818CF8"),
    ("gestion-migracion", "Gestión y migración", "#CBD5E1"),
    ("web-especializados", "Web, apps y especializados", "#2DD4BF"),
]
NOMBRE_FAMILIA = {k: n for k, n, _ in FAMILIAS}
COLOR_FAMILIA = {k: c for k, _, c in FAMILIAS}

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_corta(iso: str) -> str:
    """'2027-03-31' -> '31-mar-2027'; '2026-09' -> 'sep-2026'."""
    if not iso:
        return ""
    partes = [int(p) for p in iso.split("-")]
    if len(partes) == 3:
        return f"{partes[2]}-{MESES[partes[1] - 1]}-{partes[0]}"
    return f"{MESES[partes[1] - 1]}-{partes[0]}"


def estado_md(s: dict) -> str:
    nuevo = " 🆕" if s["nuevo"] == "1" else ""
    e = s["estado"]
    if e == "GA":
        return "🟢 GA" + nuevo
    if e == "Preview":
        return "🟡 Preview" + nuevo
    if e == "Mixto":
        return "🟢/🟡 GA y preview" + nuevo
    if e == "Retiro":
        return f"🟠 Retiro {fecha_corta(s['fecha'])}".rstrip()
    if e == "Retirado":
        return f"⛔ Retirado {fecha_corta(s['fecha'])}"
    return "ℹ️ Ver ciclo de vida"


def clave_orden(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def leer_servicios() -> list[dict]:
    with CSV.open(encoding="utf-8") as f:
        servicios = list(csv.DictReader(f))
    desconocidas = {s["familia"] for s in servicios} - set(NOMBRE_FAMILIA)
    if desconocidas:
        raise SystemExit(f"Familias desconocidas en el CSV: {desconocidas}")
    return servicios


# --------------------------------------------------------------------------- catálogo

def generar_catalogo(servicios: list[dict]) -> str:
    total = len(servicios)
    activos = [s for s in servicios if s["estado"] in {"GA", "Preview", "Mixto", "Ver"}]

    lineas = [
        '<div align="center">',
        "",
        "# 17 · Catálogo A–Z de servicios de Azure",
        "",
        f"**{total} servicios, productos y capacidades con su familia, estado y capítulo · edición {EDICION}**",
        "",
        "[⬅ 16 · Guías de decisión](16-guias-de-decision.md) · [🏠 Índice](../README.md) · "
        "[18 · Retiros ➡](18-retiros-y-ciclo-de-vida.md)",
        "",
        "</div>",
        "",
        "> [!NOTE]",
        "> Este archivo se **genera automáticamente** desde [`data/servicios.csv`](../data/servicios.csv) con",
        "> `python3 tools/generar_atlas.py`. Para corregir o añadir un servicio, edita el CSV y vuelve a ejecutar el script.",
        "",
        '<a href="../assets/azure-atlas-tabla-periodica.svg">'
        '<img src="../assets/azure-atlas-tabla-periodica.svg" '
        'alt="Tabla periódica de servicios de Azure" width="100%"></a>',
        "",
        "## Resumen por familia",
        "",
        "| Familia | GA | Preview o mixto | Verificar ciclo | En retiro | Retirados | Total |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    por_familia: dict[str, Counter] = defaultdict(Counter)
    for s in servicios:
        por_familia[s["familia"]][s["estado"]] += 1
    totales = [0] * 5
    for clave, nombre, _ in FAMILIAS:
        c = por_familia[clave]
        fila = [c["GA"], c["Preview"] + c["Mixto"], c["Ver"], c["Retiro"], c["Retirado"]]
        totales = [t + v for t, v in zip(totales, fila)]
        lineas.append(f"| {nombre} | " + " | ".join(map(str, fila)) + f" | {sum(fila)} |")
    lineas.append("| **Total** | " + " | ".join(f"**{t}**" for t in totales) + f" | **{total}** |")
    lineas += [
        "",
        "**Leyenda:** 🟢 GA · 🟡 Preview · 🟢/🟡 capacidades en GA y en preview · 🟠 en retiro (fecha de retiro) · "
        "⛔ retirado · ℹ️ verifica el ciclo de vida del SKU · 🆕 novedad 2025–2026.",
        "",
        f"Servicios activos (GA, preview o por verificar): **{len(activos)}** · en retiro o retirados: "
        f"**{total - len(activos)}**.",
        "",
    ]

    por_letra: dict[str, list[dict]] = defaultdict(list)
    for s in sorted(servicios, key=lambda x: clave_orden(x["orden"])):
        por_letra[clave_orden(s["orden"])[0].upper()].append(s)
    letras = sorted(por_letra)
    lineas += ["## Índice alfabético", "", " · ".join(f"[{l}](#{l.lower()})" for l in letras), ""]

    for letra in letras:
        lineas += [f"## {letra}", "", "| Servicio | Familia | Estado | Qué es | Cap. |", "|---|---|---|---|---|"]
        for s in por_letra[letra]:
            capitulo = s["capitulo"]
            numero = capitulo.split("-")[0]
            lineas.append(
                f"| **{s['nombre']}** | {NOMBRE_FAMILIA[s['familia']]} | {estado_md(s)} | "
                f"{s['descripcion']} | [{numero}]({capitulo}) |"
            )
        lineas.append("")

    lineas += [
        "---",
        "",
        '<div align="center">',
        "",
        "[⬅ 16 · Guías de decisión](16-guias-de-decision.md) · [🏠 Índice](../README.md) · "
        "[18 · Retiros ➡](18-retiros-y-ciclo-de-vida.md)",
        "",
        "</div>",
        "",
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- póster SVG

ANCHO_TILE, ALTO_TILE = 92, 70
PASO_X, PASO_Y = 98, 76
FILAS_MAX = 12
SEP_FAMILIA = 18
MARGEN_X, Y_CUADRICULA = 56, 214
FUENTE = "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"


def tile_svg(s: dict, x: float, y: float, numero: int, color: str) -> list[str]:
    partes = [
        f'<g transform="translate({x:.0f},{y:.0f})">',
        f'<rect width="{ANCHO_TILE}" height="{ALTO_TILE}" rx="9" fill="{color}" fill-opacity="0.13" '
        f'stroke="{color}" stroke-opacity="0.85" stroke-width="1.2"/>',
        f'<text x="7" y="13" font-size="8.5" fill="#94A3B8">{numero}</text>',
        f'<text x="{ANCHO_TILE / 2}" y="35" text-anchor="middle" font-size="21" font-weight="700" '
        f'fill="{color}">{escape(s["simbolo"])}</text>',
    ]
    if s["nuevo"] == "1":
        partes.append(f'<text x="{ANCHO_TILE - 7}" y="14" text-anchor="end" font-size="11" fill="#FDE68A">✦</text>')
    if s["estado"] in {"Preview", "Mixto"}:
        cx = ANCHO_TILE - (20 if s["nuevo"] == "1" else 9)
        partes.append(f'<circle cx="{cx}" cy="10" r="3.4" fill="#FBBF24"/>')
    lineas = s["etiqueta"].split("|")
    y0 = 52 if len(lineas) == 2 else 57
    for i, texto in enumerate(lineas):
        partes.append(
            f'<text x="{ANCHO_TILE / 2}" y="{y0 + i * 10}" text-anchor="middle" font-size="8.4" '
            f'fill="#CBD5E1">{escape(texto)}</text>'
        )
    partes.append("</g>")
    return partes


def encabezado_familia(nombre: str, x: float, ancho: float, color: str) -> list[str]:
    """Rótulo de familia que cabe en el ancho de sus columnas: reduce la fuente o usa dos líneas."""
    texto = nombre.upper()

    def cabe(linea: str, tam: float) -> bool:
        return len(linea) * tam * 0.68 <= ancho

    tam, lineas = 10.5, [texto]
    while not cabe(texto, tam) and tam > 9:
        tam -= 0.5
    if not cabe(texto, tam):
        palabras = texto.split(" ")
        cortes = [(" ".join(palabras[:i]), " ".join(palabras[i:])) for i in range(1, len(palabras))]
        lineas = list(min(cortes, key=lambda par: max(len(par[0]), len(par[1]))))
        tam = 10.5
        while not all(cabe(l, tam) for l in lineas) and tam > 7.5:
            tam -= 0.5
    y_base = Y_CUADRICULA - 22 - 12 * (len(lineas) - 1)
    return [
        f'<text x="{x + ancho / 2:.0f}" y="{y_base + i * 12}" text-anchor="middle" font-size="{tam}" '
        f'font-weight="700" fill="{color}">{escape(linea)}</text>'
        for i, linea in enumerate(lineas)
    ]


def generar_poster(servicios: list[dict]) -> str:
    en_poster = [s for s in servicios if s["poster"] == "1"]
    grupos = {clave: [s for s in en_poster if s["familia"] == clave] for clave, _, _ in FAMILIAS}

    cuerpo: list[str] = []
    x = MARGEN_X
    numero = 1
    max_filas = 0
    for clave, nombre, color in FAMILIAS:
        items = grupos[clave]
        if not items:
            continue
        columnas = math.ceil(len(items) / FILAS_MAX)
        filas = math.ceil(len(items) / columnas)
        max_filas = max(max_filas, filas)
        ancho = columnas * PASO_X - (PASO_X - ANCHO_TILE)
        cuerpo += encabezado_familia(nombre, x, ancho, color)
        cuerpo.append(
            f'<rect x="{x}" y="{Y_CUADRICULA - 14}" width="{ancho}" height="3" rx="1.5" fill="{color}" '
            f'fill-opacity="0.8"/>'
        )
        for i, s in enumerate(items):
            col, fila = divmod(i, filas)
            cuerpo += tile_svg(s, x + col * PASO_X, Y_CUADRICULA + fila * PASO_Y, numero, color)
            numero += 1
        x += ancho + SEP_FAMILIA

    ancho_total = x - SEP_FAMILIA + MARGEN_X
    y_leyenda = Y_CUADRICULA + max_filas * PASO_Y + 34
    alto_total = y_leyenda + 150

    total_servicios = len(servicios)
    familias_con_items = sum(1 for clave, _, _ in FAMILIAS if grupos[clave])
    cabecera = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho_total:.0f} {alto_total:.0f}" '
        f'width="{ancho_total:.0f}" height="{alto_total:.0f}" font-family="{FUENTE}" role="img" '
        f'aria-labelledby="t d">',
        '<title id="t">Azure Atlas · Tabla periódica de servicios de Microsoft Azure</title>',
        f'<desc id="d">{len(en_poster)} servicios activos de Azure agrupados en {familias_con_items} familias, '
        f'edición {EDICION}.</desc>',
        "<defs>",
        '<linearGradient id="fondo" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#050816"/><stop offset="0.55" stop-color="#0A1630"/>'
        '<stop offset="1" stop-color="#0B2545"/></linearGradient>',
        '<radialGradient id="halo" cx="0.18" cy="0.08" r="0.65">'
        '<stop offset="0" stop-color="#0078D4" stop-opacity="0.35"/>'
        '<stop offset="1" stop-color="#0078D4" stop-opacity="0"/></radialGradient>',
        '<pattern id="puntos" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="1.5" cy="1.5" r="1.1" fill="#FFFFFF" fill-opacity="0.05"/></pattern>',
        '<linearGradient id="marca" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#50E6FF"/><stop offset="1" stop-color="#0078D4"/></linearGradient>',
        "</defs>",
        f'<rect width="{ancho_total:.0f}" height="{alto_total:.0f}" fill="url(#fondo)"/>',
        f'<rect width="{ancho_total:.0f}" height="{alto_total:.0f}" fill="url(#halo)"/>',
        f'<rect width="{ancho_total:.0f}" height="{alto_total:.0f}" fill="url(#puntos)"/>',
        # Marca: hexágono estilizado
        f'<g transform="translate({MARGEN_X},48)">'
        '<path d="M28 0 L56 16 L56 48 L28 64 L0 48 L0 16 Z" fill="none" stroke="url(#marca)" stroke-width="3"/>'
        '<path d="M28 14 L44 23 L44 41 L28 50 L12 41 L12 23 Z" fill="url(#marca)" fill-opacity="0.35"/>'
        '<circle cx="28" cy="32" r="5" fill="#50E6FF"/></g>',
        f'<text x="{MARGEN_X + 76}" y="86" font-size="46" font-weight="800" letter-spacing="7" '
        f'fill="#F8FAFC">AZURE ATLAS</text>',
        f'<text x="{MARGEN_X + 78}" y="118" font-size="18" fill="#94A3B8">Tabla periódica de servicios de '
        f'Microsoft Azure · edición {EDICION}</text>',
    ]
    # Píldoras de cifras
    pildoras = [
        f"{len(en_poster)} servicios activos",
        f"{familias_con_items} familias",
        f"{total_servicios} entradas en el catálogo",
        "70+ regiones",
    ]
    px = ancho_total - MARGEN_X
    for texto in reversed(pildoras):
        w = 16 + len(texto) * 7.6
        px -= w
        cabecera.append(
            f'<g transform="translate({px:.0f},62)"><rect width="{w:.0f}" height="32" rx="16" fill="#0F2747" '
            f'stroke="#1E4E8C"/><text x="{w / 2:.0f}" y="21" text-anchor="middle" font-size="13" '
            f'fill="#E2E8F0">{escape(texto)}</text></g>'
        )
        px -= 12

    # Leyenda
    leyenda = [
        f'<line x1="{MARGEN_X}" y1="{y_leyenda - 14}" x2="{ancho_total - MARGEN_X:.0f}" y2="{y_leyenda - 14}" '
        f'stroke="#1E3A5F"/>'
    ]
    lx, ly = MARGEN_X, y_leyenda + 10
    for i, (clave, nombre, color) in enumerate(FAMILIAS):
        if not grupos[clave]:
            continue
        col, fila = i % 7, i // 7
        gx, gy = lx + col * 250, ly + fila * 30
        leyenda.append(
            f'<rect x="{gx}" y="{gy}" width="16" height="16" rx="4" fill="{color}" fill-opacity="0.25" '
            f'stroke="{color}"/><text x="{gx + 24}" y="{gy + 13}" font-size="13" fill="#E2E8F0">'
            f"{escape(nombre)} ({len(grupos[clave])})</text>"
        )
    ly2 = ly + 74
    leyenda += [
        f'<text x="{lx}" y="{ly2}" font-size="13" fill="#FDE68A">✦</text>'
        f'<text x="{lx + 18}" y="{ly2}" font-size="13" fill="#CBD5E1">Novedad 2025–2026</text>',
        f'<circle cx="{lx + 196}" cy="{ly2 - 4}" r="4" fill="#FBBF24"/>'
        f'<text x="{lx + 208}" y="{ly2}" font-size="13" fill="#CBD5E1">Preview o capacidades en preview</text>',
        f'<text x="{ancho_total - MARGEN_X:.0f}" y="{ly2}" text-anchor="end" font-size="12" fill="#64748B">'
        "Fuente: data/servicios.csv · generado con tools/generar_atlas.py</text>",
    ]
    return "\n".join(cabecera + cuerpo + leyenda + ["</svg>", ""])


# --------------------------------------------------------------------------- banner SVG

# Nodos del banner: (id, símbolo, nombre, x, y, color). Representan los cinco pilares del capítulo 02.
NODOS_BANNER = [
    ("usr", "", "Usuarios", 905, 200, "#E2E8F0"),
    ("fd", "Fd", "Front Door", 1010, 150, "#34D399"),
    ("lb", "Lb", "Load Balancer", 1010, 280, "#34D399"),
    ("aks", "Aks", "AKS", 1135, 120, "#22D3EE"),
    ("aca", "Aca", "Container Apps", 1135, 240, "#22D3EE"),
    ("sb", "Sb", "Service Bus", 1260, 150, "#FB923C"),
    ("eh", "Eh", "Event Hubs", 1260, 280, "#FB923C"),
    ("fn", "Fn", "Functions", 1380, 215, "#60A5FA"),
    ("cdb", "Cdb", "Cosmos DB", 1500, 140, "#E879F9"),
    ("st", "St", "Storage", 1500, 290, "#A78BFA"),
]
ARISTAS_BANNER = [
    ("usr", "fd", False), ("fd", "aks", False), ("fd", "aca", False), ("fd", "lb", True), ("lb", "aca", True),
    ("aca", "sb", False), ("aks", "eh", False), ("sb", "fn", False), ("eh", "fn", False),
    ("fn", "cdb", False), ("fn", "st", False),
]


def generar_banner(servicios: list[dict]) -> str:
    ancho, alto = 1600, 420
    pos = {n[0]: (n[3], n[4]) for n in NODOS_BANNER}
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}" '
        f'font-family="{FUENTE}" role="img" aria-labelledby="bt">',
        "<title id=\"bt\">Azure Atlas · Guía técnica definitiva de Microsoft Azure</title>",
        "<defs>",
        '<linearGradient id="bfondo" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#050816"/><stop offset="0.6" stop-color="#0A1630"/>'
        '<stop offset="1" stop-color="#0B2545"/></linearGradient>',
        '<radialGradient id="bhalo" cx="0.78" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#0078D4" stop-opacity="0.35"/>'
        '<stop offset="1" stop-color="#0078D4" stop-opacity="0"/></radialGradient>',
        '<pattern id="bpuntos" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="1.5" cy="1.5" r="1.1" fill="#FFFFFF" fill-opacity="0.05"/></pattern>',
        '<linearGradient id="bmarca" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#50E6FF"/><stop offset="1" stop-color="#0078D4"/></linearGradient>',
        '<filter id="brillo" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#7DD3FC" fill-opacity="0.8"/></marker>',
        "</defs>",
        f'<rect width="{ancho}" height="{alto}" fill="url(#bfondo)"/>',
        f'<rect width="{ancho}" height="{alto}" fill="url(#bhalo)"/>',
        f'<rect width="{ancho}" height="{alto}" fill="url(#bpuntos)"/>',
        # Marca y título
        '<g transform="translate(72,96)">'
        '<path d="M34 0 L68 19 L68 58 L34 77 L0 58 L0 19 Z" fill="none" stroke="url(#bmarca)" stroke-width="3.5"/>'
        '<path d="M34 17 L53 28 L53 50 L34 61 L15 50 L15 28 Z" fill="url(#bmarca)" fill-opacity="0.35"/>'
        '<circle cx="34" cy="39" r="6" fill="#50E6FF"/></g>',
        '<text x="164" y="160" font-size="64" font-weight="800" letter-spacing="10" fill="#F8FAFC">AZURE ATLAS</text>',
        '<text x="166" y="204" font-size="25" fill="#CBD5E1">Guía técnica definitiva de Microsoft Azure</text>',
        f'<text x="166" y="238" font-size="16" fill="#94A3B8">Sistemas distribuidos · {len(servicios)} servicios '
        f'catalogados · 19 capítulos · edición {EDICION}</text>',
    ]
    pilares = [("① Cómputo", "#22D3EE"), ("② Datos", "#E879F9"), ("③ Mensajería", "#FB923C"),
               ("④ Enrutamiento", "#34D399"), ("⑤ Observabilidad", "#818CF8")]
    px = 166
    for texto, color in pilares:
        w = 22 + len(texto) * 8.2
        partes.append(
            f'<g transform="translate({px:.0f},276)"><rect width="{w:.0f}" height="34" rx="17" fill="{color}" '
            f'fill-opacity="0.14" stroke="{color}" stroke-opacity="0.9"/><text x="{w / 2:.0f}" y="22.5" '
            f'text-anchor="middle" font-size="14.5" font-weight="600" fill="{color}">{escape(texto)}</text></g>'
        )
        px += w + 10
    # Banda de observabilidad (pilar ⑤) bajo el diagrama
    partes += [
        '<rect x="960" y="352" width="590" height="34" rx="17" fill="#818CF8" fill-opacity="0.12" '
        'stroke="#818CF8" stroke-opacity="0.8" stroke-dasharray="5 4"/>',
        '<text x="1255" y="374" text-anchor="middle" font-size="13.5" fill="#C7D2FE">Azure Monitor · '
        'Application Insights · OpenTelemetry</text>',
    ]
    for origen in ("aca", "fn", "st"):
        ox, oy = pos[origen]
        partes.append(f'<line x1="{ox}" y1="{oy + 30}" x2="{ox}" y2="352" stroke="#818CF8" stroke-opacity="0.55" '
                      f'stroke-dasharray="3 4"/>')
    # Aristas
    for a, b, punteada in ARISTAS_BANNER:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        d = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        x1, y1, x2, y2 = x1 + ux * 30, y1 + uy * 30, x2 - ux * 32, y2 - uy * 32
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        estilo = ' stroke-dasharray="6 5"' if punteada else ""
        partes.append(
            f'<path d="M{x1:.0f} {y1:.0f} Q{cx:.0f} {cy:.0f} {x2:.0f} {y2:.0f}" fill="none" stroke="#7DD3FC" '
            f'stroke-opacity="0.55" stroke-width="2"{estilo} marker-end="url(#flecha)"/>'
        )
    # Nodos
    for clave, simbolo, nombre, x, y, color in NODOS_BANNER:
        partes += [
            f'<circle cx="{x}" cy="{y}" r="27" fill="{color}" fill-opacity="0.22" filter="url(#brillo)"/>',
            f'<circle cx="{x}" cy="{y}" r="27" fill="#0B1B33" stroke="{color}" stroke-width="2"/>',
            f'<text x="{x}" y="{y + 46}" text-anchor="middle" font-size="12" fill="#E2E8F0">{escape(nombre)}</text>',
        ]
        if clave == "usr":  # icono de persona dibujado (sin depender de fuentes de emoji)
            partes.append(
                f'<circle cx="{x}" cy="{y - 6}" r="6.5" fill="{color}"/>'
                f'<path d="M{x - 12} {y + 14} Q{x} {y - 4} {x + 12} {y + 14} Z" fill="{color}"/>'
            )
        else:
            partes.append(
                f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-size="16" font-weight="700" '
                f'fill="{color}">{escape(simbolo)}</text>'
            )
    partes += ["</svg>", ""]
    return "\n".join(partes)


def main() -> None:
    servicios = leer_servicios()
    CATALOGO.write_text(generar_catalogo(servicios), encoding="utf-8")
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    POSTER.write_text(generar_poster(servicios), encoding="utf-8")
    BANNER.write_text(generar_banner(servicios), encoding="utf-8")
    print(f"{len(servicios)} servicios → {CATALOGO.relative_to(RAIZ)}, {POSTER.relative_to(RAIZ)} "
          f"y {BANNER.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
