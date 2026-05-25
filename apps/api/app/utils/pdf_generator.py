import io
import os

from fpdf import FPDF

_FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


class _LiabilityPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", os.path.join(_FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", "I", os.path.join(_FONT_DIR, "DejaVuSans-Oblique.ttf"))
        self.add_font("DejaVu", "BI", os.path.join(_FONT_DIR, "DejaVuSans-BoldOblique.ttf"))

    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(26, 43, 34)
        self.cell(0, 10, "LA JUANA COLOMBIA", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "B", 12)
        self.cell(0, 8, "RENUNCIA Y LIBERACIÓN DE RECLAMOS Y RESPONSABILIDADES", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def generate_liability_release_pdf(text: str, participant_name: str) -> bytes:
    pdf = _LiabilityPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(30, 30, 30)

    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        clean = paragraph.strip()
        if clean:
            pdf.multi_cell(0, 6, clean)
            pdf.ln(2)
        else:
            pdf.ln(4)

    pdf.ln(8)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 6, "Nombre del participante que acepta:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 6, participant_name, new_x="LMARGIN", new_y="NEXT")

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
