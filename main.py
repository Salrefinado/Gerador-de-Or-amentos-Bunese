from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io, json, os, re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import yellow
from PyPDF2 import PdfReader, PdfWriter
from datetime import date, datetime
import locale
from html.parser import HTMLParser

# --- Bloco de configuração inicial ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não encontrado. O mês extenso pode não funcionar.")
        pass

APP_DIR = os.path.dirname(__file__)
TEMPLATE_PATH_DEFAULT = os.path.join(APP_DIR, "Orçamento 2.0.pdf")
POSITIONS_FILE = os.path.join(APP_DIR, "positions.json")
TEMPLATE_UPLOAD_PATH = os.path.join(APP_DIR, "uploaded_template.pdf")
STATIC_DIR = os.path.join(APP_DIR, "static")

os.makedirs(STATIC_DIR, exist_ok=True) 

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

ITEM_DEFINITIONS = {
    "Tampa Inox": "Tampa para churrasqueira em aço inox 304.\n    Custo R$ 8.600,00",
    "Tampa Epoxi": "Tampa para churrasqueira em chapa galvanizada com pintura preta EPOXI.",
    "Revestimento Fundo": "Revestimento interno fundo em aço inox 304.",
    "Revestimento Em L": "Revestimento interno fundo e uma lateral em aço inox 304.",
    "Revestimento Em U": "Revestimento interno fundo e duas laterais em aço inox 304.",
    "Sistema de Elevar Manual 2 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, em vergalhão 3/16. Material aço inox 304.",
    "Sistema de Elevar Manual 1/8 e 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.",
    "Sistema de Elevar Manual Arg e 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.",
    "Sistema de Elevar Manual Arg e 1/8": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.",
    "Sistema de Elevar Motor 2 3/16": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, em vergalhão 3/16. Material aço inox 304.",
    "Sistema de Elevar Motor 1/8 e 3/16": "Sistema de elevar grelhas ccomando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.",
    "Sistema de Elevar Motor Arg e 3/16": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.",
    "Sistema de Elevar Motor Arg e 1/8": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.",
    "Giratório 1L 4E": "Sistema giratório de espetos com 1 linha de 4 espetos. Material aço inox 304.",
    "Giratório 1L 5E": "Sistema giratório de espetos com 1 linha de 5 espetos. Material aço inox 304.",
    "Giratório 2L 5E": "Sistema giratório de espetos com 2 linhas de 5 espetos. Material aço inox 304.",
    "Giratório 2L 6E": "Sistema giratório de espetos com 2 linha de 6 espetos. Material aço inox 304.",
    "Giratório 2L 7E": "Sistema giratório de espetos com 2 linha de 7 espetos. Material aço inox 304.",
    "Giratório 2L 8E": "Sistema giratório de espetos com 2 linha de 8 espetos. Material aço inox 304.",
    "Cooktop + Bifeira": "Fogareiro Cooktop Tramontina tripla chama modificado com Bifeira Grill de 4mm em aço inox 304.",
    "Cooktop": "Fogareiro Cooktop Tramontina tripla chama modificado em aço inox 304.",
    "Porta Guilhotina Vidro L": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal e uma lateral fixa. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.",
    "Porta Guilhotina Vidro U": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal e duas laterais fixas. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.",
    "Porta Guilhotina Vidro F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.",
    "Porta Guilhotina Inox F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento em INOX. Material: Base em aço inox 304 e superior em Metalon galvanizado.",
    "Porta Guilhotina Pedra F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e  fechamento em pedra fornecida pelo cliente. Material: Base em aço inox 304 e superior em Metalon galvanizado.",
    "Coifa Epoxi": "Coifa interna para churrasqueira abrangendo a área de carvão, com 0 metros de dutos internos. Material:chapa galvanizada com pintura epóxi preta.",
    "Isolamento Coifa": "Isolamento térmico de coifa com manta de fibra cerâmica.",
    "Placa cimenticia Porta": "Aplicação de placa cimentícia sob porta guilhotina para fechamento e para receber o revestimento final.",
    "Revestimento Base": "Revestimento na base inferior da churrasqueira com placa cimentícia e manta de fibra cerâmica. (item recomendável para proteger marcenaria).",
    "Bifeteira grill": "Chapa bifeteira grill (adicional) para sistema de elevar.",
    "Balanço 2": "Regulagens de espetos em balanço 2 estágios. Material aço inox 304.",
    "Balanço 3": "Regulagens de espetos em balanço 3 estágios. Material aço inox 304.",
    "Balanço 4": "Regulagens de espetos em balanço 4 estágios. Material aço inox 304.",
    "Kit 6 Espetos": "Jogo de espetos 6 unidades sob medida com cabos em inox.",
    "Regulagem Comum 2": "Regulagem de espetos frente e fundo com 2 estágios. Material aço inox 304.",
    "Regulagem Comum 3": "Regulagem de espetos frente e fundo com 3 estágios. Material aço inox 304.",
    "Regulagem Comum 4": "Regulagem de espetos frente e fundo com 4 estágios. Material aço inox 304.",
    "Regulagem Comum 5": "Regulagem de espetos frente e fundo com 5 estágios. Material aço inox 304.",
    "Regulagem Comum 3": "Regulagem de espetos frente e fundo com 3 estágios. Material aço inox 304.",
    "Gavetão Inox": "Gavetão inferior a churrasqueira com corrediças e rodízios. Material: chapa galvanizada interno, e frontão em aço inox 304.",
    "Moldura Área de fogo": "Moldura área de fogo em aço inox 304. Material: aço inox 304.",
    "Grelha de descanso": "Grelha de descanso",
    "KAM800 2 Faces": "Lareira Kaminofen Modelo KAM800 DUPLA FACE com potência de 380m³. Material: Aço carbono 3mm com pintura preto alta temperatura, vidro cerâmico ShotRobax cordas de vedação do vidro e portas são importados.",
}
DEFAULT_POSITIONS = {
    "numero": {"x": 450, "y": 760, "size": 10}, "data": {"x": 480, "y": 760, "size": 10},
    "responsavelObra": {"x": 60, "y": 740, "size": 10}, "telefoneResponsavel": {"x": 220, "y": 740, "size": 10}, 
    "cliente": {"x": 60, "y": 720, "size": 10}, "telefone": {"x": 220, "y": 720, "size": 10}, 
    "cpf": {"x": 220, "y": 700, "size": 10}, "rg": {"x": 60, "y": 700, "size": 10}, 
    "arquiteto": {"x": 60, "y": 680, "size": 10}, "projeto": {"x": 220, "y": 680, "size": 10}, 
    "enderecoObra": {"x": 60, "y": 660, "size": 10}, 
    "itemsStart": {"x": 42, "y": 527, "size": 13}, "lineHeight": 25
}

def load_positions():
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return DEFAULT_POSITIONS.copy()

# --- Classe para "traduzir" HTML para o PDF (versão final robusta) ---
class PDFHTMLParser(HTMLParser):
    def __init__(self, canvas, x, y, size, line_height, max_x, is_etapa=False):
        super().__init__()
        self.c = canvas
        self.x = x
        self.y = y
        self.initial_x = x
        self.size = size
        self.line_height = line_height
        self.wrapped_line_height = size * 1.4
        self.max_x = max_x
        self.is_etapa = is_etapa
        self.style_stack = [{'bold': False, 'highlight': False}]

    def handle_starttag(self, tag, attrs):
        new_style = self.style_stack[-1].copy()
        
        if tag in ['b', 'strong']:
            new_style['bold'] = True
            
        attrs_dict = dict(attrs)
        if 'style' in attrs_dict:
            style_str = attrs_dict['style'].replace(' ', '').lower()
            if 'font-weight:bold' in style_str or 'font-weight:700' in style_str:
                new_style['bold'] = True
            if 'background-color:yellow' in style_str:
                new_style['highlight'] = True
                
        self.style_stack.append(new_style)

    def handle_endtag(self, tag):
        if len(self.style_stack) > 1:
            self.style_stack.pop()

    def handle_data(self, data):
        current_style = self.style_stack[-1]
        font_name = "Helvetica-Bold" if self.is_etapa or current_style['bold'] else "Helvetica"
        self.c.setFont(font_name, self.size)
        
        parts = re.split('(\\s+)', data)
        for part in parts:
            if not part: continue
            is_space = part.isspace()
            part_width = self.c.stringWidth(part, font_name, self.size)

            if not is_space and self.x + part_width > self.max_x:
                if self.x > self.initial_x:
                    self.x = self.initial_x
                    self.y -= self.wrapped_line_height

            if current_style['highlight'] and not is_space:
                self.c.setFillColor(yellow)
                self.c.rect(self.x, self.y - 2, part_width, self.size, stroke=0, fill=1)
                self.c.setFillColorRGB(0, 0, 0)
                
            self.c.drawString(self.x, self.y, part)
            self.x += part_width

# --- Função reutilizável para desenhar texto com quebra de linha ---
def draw_wrapped_text(canvas, text, x, y, size, max_width):
    canvas.setFont("Helvetica", size)
    lines = []
    words = text.split()
    if not words: return
    current_line = words[0]
    for word in words[1:]:
        if canvas.stringWidth(f"{current_line} {word}", "Helvetica", size) < max_width:
            current_line += f" {word}"
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    line_height = size * 1.2
    for line in lines:
        canvas.drawString(x, y, line)
        y -= line_height

# --- Rotas da aplicação ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, "positions": load_positions(), 
        "today": date.today().isoformat(), "template_exists": get_template_path() is not None, 
        "item_definitions": ITEM_DEFINITIONS
    })

def get_template_path():
    if os.path.exists(TEMPLATE_UPLOAD_PATH): return TEMPLATE_UPLOAD_PATH
    if os.path.exists(TEMPLATE_PATH_DEFAULT): return TEMPLATE_PATH_DEFAULT
    return None

@app.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    with open(TEMPLATE_UPLOAD_PATH, "wb") as f: f.write(await file.read())
    return RedirectResponse(url="/", status_code=303)

@app.post("/save-positions")
async def api_save_positions(request: Request):
    data = await request.json()
    with open(POSITIONS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    return {"ok": True}

# --- Rota de Geração de PDF ---
@app.post("/generate")
async def generate_pdf(
    numero: str = Form(""), data: str = Form(""), responsavelObra: str = Form(""),
    telefoneResponsavel: str = Form(""), cliente: str = Form(""), cpf: str = Form(""),
    rg: str = Form(""), enderecoObra: str = Form(""), telefone: str = Form(""),
    arquiteto: str = Form(""), projeto: str = Form(""), items: str = Form("")
):
    template_path = get_template_path()
    if not template_path: return {"error": "Nenhum template disponível."}
    
    positions = load_positions()
    
    data_formatada_pdf = data 
    try: data_formatada_pdf = datetime.strptime(data, '%Y-%m-%d').date().strftime("%d de %B de %Y").replace(" de 0", " de ")
    except ValueError: pass

    def clean(s): return "".join(c for c in s.strip().replace("/", "_").replace("\\", "_") if c.isalnum() or c in (' ', '_', '.'))
    
    prefixo_projeto = f"{clean(projeto)} " if clean(projeto) and clean(projeto).upper() not in ("N/A", "NA", "NÃO SE APLICA") else ""
    filename = f"Orçamento {clean(numero)} {prefixo_projeto}cliente {clean(cliente)}.pdf"
    
    packet = io.BytesIO()
    try:
        tpl_reader = PdfReader(template_path)
        page_width, page_height = float(tpl_reader.pages[0].mediabox.width), float(tpl_reader.pages[0].mediabox.height)
    except Exception: page_width, page_height = letter
    
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    def draw_text_at(key, text):
        if not text: return
        p = positions.get(key)
        if not p: return
        c.setFont("Helvetica", p.get("size", 10))
        c.drawString(p.get("x", 50), p.get("y", 750), str(text)[:200])
        
    numero_pos = positions.get("numero")
    if numero_pos and numero:
        c.setFont("Helvetica-Bold", numero_pos.get("size", 10))
        c.drawString(numero_pos.get("x", 50), numero_pos.get("y", 750), str(numero))

    draw_text_at("data", data_formatada_pdf)
    draw_text_at("responsavelObra", responsavelObra); draw_text_at("telefoneResponsavel", telefoneResponsavel)
    draw_text_at("cliente", cliente); draw_text_at("cpf", cpf); draw_text_at("rg", rg)
    draw_text_at("telefone", telefone)
    draw_text_at("arquiteto", arquiteto or "N/A"); draw_text_at("projeto", projeto or "N/A")

    addr_pos = positions.get("enderecoObra")
    if addr_pos and enderecoObra:
        max_width_addr = page_width - addr_pos.get("x", 60) - 25
        draw_wrapped_text(c, enderecoObra, addr_pos.get("x", 60), addr_pos.get("y", 660), addr_pos.get("size", 10), max_width_addr)

    items_list = [s.strip() for s in items.splitlines() if s.strip()]
    x_items = positions.get("itemsStart", {}).get("x", 60)
    y_items = positions.get("itemsStart", {}).get("y", 560)
    line_h = positions.get("lineHeight", 25)
    size = positions.get("itemsStart", {}).get("size", 13)
    
    y_cursor, numbered_item_index = y_items, 0
    
    for item_line in items_list:
        is_etapa = item_line.startswith("@@ETAPA_START@@")
        
        # Separa a descrição do custo, se houver
        processed_line = item_line.replace("@@ETAPA_START@@", "").strip()
        parts = processed_line.split('\n', 1)
        html_description = parts[0]
        cost_line = parts[1].strip() if len(parts) > 1 else None

        # Desenha o prefixo (A), B), etc) se não for uma etapa
        start_x, prefix_width = x_items, 0
        if not is_etapa:
            numbered_item_index += 1
            letter_prefix = f"{chr(65 + numbered_item_index - 1)}) "
            c.setFont("Helvetica", size)
            c.drawString(start_x, y_cursor, letter_prefix)
            prefix_width = c.stringWidth(letter_prefix, "Helvetica", size)
        
        # Posição inicial do texto (depois do prefixo)
        text_x = start_x + prefix_width
        max_x_items = page_width - x_items - 10 # Margem direita
        
        # Desenha a descrição principal (que pode ter HTML)
        parser = PDFHTMLParser(c, text_x, y_cursor, size, line_h, max_x_items, is_etapa=is_etapa)
        parser.feed(html_description)
        
        # Pega a posição Y final após desenhar a descrição
        y_after_description = parser.y
        
        # Se houver uma linha de custo, desenha-a logo abaixo
        if cost_line and not is_etapa:
            y_for_cost = y_after_description - (size * 1.2) # Posição um pouco abaixo
            c.setFont("Helvetica-Bold", size - 1) # Fonte em negrito
            c.drawString(text_x + 15, y_for_cost, cost_line) # Desenha com recuo
            # A posição do cursor para o próximo item começa abaixo do custo
            y_cursor = y_for_cost - line_h
        else:
            # Se não houver custo, o próximo item começa abaixo da descrição
            y_cursor = y_after_description - line_h
        
    c.save()
    packet.seek(0)
    
    overlay_reader = PdfReader(packet)
    writer = PdfWriter()
    tpl_reader = PdfReader(template_path)
    tpl_page = tpl_reader.pages[0]
    tpl_page.merge_page(overlay_reader.pages[0])
    writer.add_page(tpl_page)
    
    for i in range(1, len(tpl_reader.pages)): writer.add_page(tpl_reader.pages[i])
        
    out_bytes = io.BytesIO()
    writer.write(out_bytes)
    out_bytes.seek(0)

    return StreamingResponse(
        out_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
    )
