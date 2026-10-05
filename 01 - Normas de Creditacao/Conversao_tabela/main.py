import pdfplumber
import pandas as pd
import re
import os

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)

# ============================================================
# REGEX
# ============================================================

TABLE1_PATTERN = re.compile(
    r"""^(?P<symbol>\S+)\s+(?P<value>0x[0-9A-Fa-f]+)\s+(?P<ovtype>.+?)\s+(?P<size>\d+)\s+(?P<object>.+)$"""
)

TABLE3_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<code>\d+)\s+
    (?P<inc>\d+)\s+
    (?P<ro>\d+)\s+
    (?P<rw>\d+)\s+
    (?P<zi>\d+)\s+
    (?P<debug>\d+)
    """,
    re.VERBOSE
)

TOTALS_PATTERN = re.compile(
    r"""
    ^Total\s+
    (?P<name>RO|RW|ROM)\s+Size
    .*?
    (?P<value>\d+)
    \s*\((?P<human>[^)]+)\)
    """,
    re.VERBOSE
)

COLUMNS_TABLE2 = {
    "Exec Addr": (80, 120),
    "Load Addr": (120, 170),
    "Size": (170, 215),
    "Type": (215, 235),
    "Attr": (235, 255),
    "Idx": (255, 275),
}

# ============================================================
# DADOS
# ============================================================

data_table1 = []
data_table2 = []
data_table3 = []
final_totals = {}

def normalize(v):
    return "" if not v or v.strip() in {"-"} else v.strip()

USER_PATH = r"C:\Users\80403185\Documents\Labelo\Conversao_tabela"
PDF_PATH = USER_PATH + r"\LAAGER_COPIA.pdf"
OUTPUT_DIR = USER_PATH + r"\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SECTION_START_X = COLUMNS_TABLE2["Idx"][1]

# ============================================================
# LEITURA DO PDF
# ============================================================

with pdfplumber.open(PDF_PATH) as pdf:
    current_table = None

    for page in pdf.pages:
        rows = {}
        for w in page.extract_words():
            y = round(w["top"] / 5) * 5
            rows.setdefault(y, []).append(w)

        for y in sorted(rows):
            row_words = sorted(rows[y], key=lambda w: w["x0"])
            line = " ".join(w["text"] for w in row_words)

            # ---------------- DETECÇÃO ----------------

            if "Object(Section)" in line:
                current_table = "T1"
                continue

            if "Exec Addr" in line and "Load Addr" in line:
                current_table = "T2"
                continue

            if "Code (inc. data)" in line:
                current_table = "T3"
                continue

            if current_table == "T1" and "=" in line:
                current_table = None
                continue

            if current_table == "T3" and line.strip().startswith("="):
                current_table = None
                continue

            # ---------------- TABELA 1 ----------------

            if current_table == "T1":
                m = TABLE1_PATTERN.match(line)
                if m:
                    data_table1.append(m.groupdict())

            # ---------------- TABELA 2 ----------------

            elif current_table == "T2":
                if (
                    "Memory Map" in line
                    or "Exec base:" in line
                    or "Load base:" in line
                ):
                    continue

                row = {}
                for col, (x0, x1) in COLUMNS_TABLE2.items():
                    row[col] = normalize(" ".join(
                        w["text"]
                        for w in row_words
                        if x0 <= (w["x0"] + w["x1"]) / 2 < x1
                    ))

                if not row["Exec Addr"]:
                    continue

                tail = [
                    w["text"]
                    for w in row_words
                    if (w["x0"] + w["x1"]) / 2 >= SECTION_START_X
                ]

                if not tail:
                    row["Section Name"] = ""
                    row["Object"] = ""
                elif tail[0] == "*":
                    row["Section Name"] = "*"
                    row["Object"] = normalize(" ".join(tail[1:]))
                elif tail[0].startswith(".ARM."):
                    row["Section Name"] = ""
                    row["Object"] = normalize(" ".join(tail))
                else:
                    row["Section Name"] = normalize(tail[0])
                    row["Object"] = normalize(" ".join(tail[1:]))

                data_table2.append(row)

            # ---------------- TABELA 3 ----------------

            elif current_table == "T3":
                m = TABLE3_PATTERN.match(line)
                if m:
                    data_table3.append({
                        "Code": m.group("code"),
                        "(inc. data)": m.group("inc"),
                        "RO Data": m.group("ro"),
                        "RW Data": m.group("rw"),
                        "ZI Data": m.group("zi"),
                        "Debug": m.group("debug"),
                    })

            # ---------------- TOTALS FINAIS ----------------

            m_total = TOTALS_PATTERN.match(line)
            if m_total:
                final_totals[m_total.group("name")] = {
                    "bytes": m_total.group("value"),
                    "human": m_total.group("human"),
                    "raw": line
                }

# ============================================================
# DATAFRAMES
# ============================================================

df1 = pd.DataFrame(data_table1)
df2 = pd.DataFrame(data_table2)
df3 = pd.DataFrame(data_table3)

# ============================================================
# EXPORTAÇÃO HTML
# ============================================================

totals_html = "<h2>Totals</h2><ul>"
for k, v in final_totals.items():
    totals_html += f"<li><b>{k}</b>: {v['bytes']} bytes ({v['human']})</li>"
totals_html += "</ul>"

html = f"""
<h2>Tabela 1</h2>{df1.to_html(index=False)}
<h2>Tabela 2</h2>{df2.to_html(index=False)}
<h2>Tabela 3</h2>{df3.to_html(index=False)}
{totals_html}
"""

with open(OUTPUT_DIR + r"\tables.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✔ OK")
print("Tabela 1:", df1.shape)
print("Tabela 2:", df2.shape)
print("Tabela 3:", df3.shape)
print("Totals:", final_totals)
