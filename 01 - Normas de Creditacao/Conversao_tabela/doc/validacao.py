import pdfplumber
import html

pdf_path = r"C:\Users\80403185\Documents\Codigos\doc\doc2.pdf"


def extract_sections(pdf_path):
    sections = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            })

            words = page.extract_words()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue

                    ct = row[0]
                    comando = row[1]

                    # pega resposta corretamente
                    resposta = ""
                    for cell in row[2:]:
                        if cell and cell.strip():
                            resposta = cell
                            break

                    # encontrar posição do CT na página
                    ct_word = None
                    for w in words:
                        if ct and ct in w["text"]:
                            ct_word = w
                            break

                    detalhes = ""

                    if ct_word:
                        y_ct = ct_word["top"]

                        # pega palavras abaixo até próximo CT
                        for w in words:
                            if w["top"] > y_ct and w["top"] < y_ct + 50:
                                if "CT" not in w["text"]:
                                    detalhes += w["text"] + " "

                    sections.append({
                        "ct": ct,
                        "comando": comando,
                        "resposta": resposta,
                        "detalhes": detalhes.strip()
                    })

    return sections


def generate_html(sections, output_file):
    html_content = """
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
    table {border-collapse: collapse; width: 100%;}
    th, td {border: 1px solid black; padding: 8px;}
    th {background-color: #eee;}
    </style>
    </head>
    <body>

    <table>
    <tr>
    <th>CT</th>
    <th>COMANDO ENVIADO</th>
    <th>RESPOSTA RECEBIDA</th>
    <th>DETALHES</th>
    </tr>
    """

    for section in sections:
        comando = html.escape(section['comando'] or "").replace('\n', '<br>')
        resposta = html.escape(section['resposta'] or "").replace('\n', '<br>')
        detalhes = html.escape(section['detalhes'] or "").replace('\n', '<br>')

        html_content += f"""
        <tr>
        <td>{section['ct']}</td>
        <td>{comando}</td>
        <td>{resposta}</td>
        <td>{detalhes}</td>
        </tr>
        """

    html_content += """
    </table>
    </body>
    </html>
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    output_html = "output_final.html"

    sections = extract_sections(pdf_path)
    generate_html(sections, output_html)

    print("HTML com detalhes gerado com sucesso!")


if __name__ == "__main__":
    main()