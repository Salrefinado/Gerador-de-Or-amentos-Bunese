from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io, json, os, re, base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import yellow
from PyPDF2 import PdfReader, PdfWriter
from datetime import date, datetime
import locale
from html.parser import HTMLParser
from PIL import Image
from database import database, orcamentos

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
TEMPLATE_PATH_PAGE2 = os.path.join(APP_DIR, "static", "Pagina Nova.pdf")
POSITIONS_FILE = os.path.join(APP_DIR, "positions.json")
POSITIONS_FILE_PAGE2 = os.path.join(APP_DIR, "positions_page2.json")
TEMPLATE_UPLOAD_PATH = os.path.join(APP_DIR, "uploaded_template.pdf")
STATIC_DIR = os.path.join(APP_DIR, "static")
REFERENCIA_DIR = os.path.join(STATIC_DIR, "Referencia")


os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(REFERENCIA_DIR, exist_ok=True)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

ITEM_DEFINITIONS = {
    "Tampa Inox": "Tampa para churrasqueira em aço inox 304.<br><b>Custo R$ 8.600,00</b>",
    "Tampa Epoxi": "Tampa para churrasqueira em chapa galvanizada com pintura preta EPOXI.<br><b>Custo R$ 4.500,00</b>",
    "Revestimento Fundo": "Revestimento interno fundo em aço inox 304.<br><b>Custo R$ 2.000,00</b>",
    "Revestimento Em L": "Revestimento interno fundo e uma lateral em aço inox 304.<br><b>Custo R$ 2.800,00</b>",
    "Revestimento Em U": "Revestimento interno fundo e duas laterais em aço inox 304.<br><b>Custo R$ 3.500,00</b>",
    "Sistema de Elevar Manual 2 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, em vergalhão 3/16. Material aço inox 304.<br><b>Custo R$ 5.500,00</b>",
    "Sistema de Elevar Manual 1/8 e 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.<br><b>Custo R$ 5.700,00</b>",
    "Sistema de Elevar Manual Arg e 3/16": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.<br><b>Custo R$ 5.800,00</b>",
    "Sistema de Elevar Manual Arg e 1/8": "Sistema de elevar grelhas comando MANUAL na manivela com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalão 1/8. Material aço inox 304.<br><b>Custo R$ 5.900,00</b>",
    "Sistema de Elevar Motor 2 3/16": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, em vergalhão 3/16. Material aço inox 304.<br><b>Custo R$ 7.500,00</b>",
    "Sistema de Elevar Motor 1/8 e 3/16": "Sistema de elevar grelhas ccomando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.<br><b>Custo R$ 7.700,00</b>",
    "Sistema de Elevar Motor Arg e 3/16": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.<br><b>Custo R$ 7.800,00</b>",
    "Sistema de Elevar Motor Arg e 1/8": "Sistema de elevar grelhas comando elétrico com quadro eixo e guias e 2 grelhas removíveis, uma em vergalhão 3/16 e outra em vergalhão 1/8. Material aço inox 304.<br><b>Custo R$ 7.900,00</b>",
    "Giratório 1L 4E": "Sistema giratório de espetos com 1 linha de 4 espetos. Material aço inox 304.<br><b>Custo R$ 4.200,00</b>",
    "Giratório 1L 5E": "Sistema giratório de espetos com 1 linha de 5 espetos. Material aço inox 304.<br><b>Custo R$ 4.500,00</b>",
    "Giratório 2L 5E": "Sistema giratório de espetos com 2 linhas de 5 espetos. Material aço inox 304.<br><b>Custo R$ 5.800,00</b>",
    "Giratório 2L 6E": "Sistema giratório de espetos com 2 linha de 6 espetos. Material aço inox 304.<br><b>Custo R$ 6.200,00</b>",
    "Giratório 2L 7E": "Sistema giratório de espetos com 2 linha de 7 espetos. Material aço inox 304.<br><b>Custo R$ 6.600,00</b>",
    "Giratório 2L 8E": "Sistema giratório de espetos com 2 linha de 8 espetos. Material aço inox 304.<br><b>Custo R$ 7.000,00</b>",
    "Cooktop + Bifeira": "Fogareiro Cooktop Tramontina tripla chama modificado com Bifeira Grill de 4mm em aço inox 304.<br><b>Custo R$ 3.800,00</b>",
    "Cooktop": "Fogareiro Cooktop Tramontina tripla chama modificado em aço inox 304.<br><b>Custo R$ 2.500,00</b>",
    "Porta Guilhotina Vidro L": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal e uma lateral fixa. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.<br><b>Custo R$ 9.500,00</b>",
    "Porta Guilhotina Vidro U": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal e duas laterais fixas. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.<br><b>Custo R$ 10.500,00</b>",
    "Porta Guilhotina Vidro F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento com vidro refletivo frontal. Material: Base em aço inox 304 e superior em Metalon galvanizado, vidro Habith Cebrace.<br><b>Custo R$ 8.500,00</b>",
    "Porta Guilhotina Inox F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e fechamento em INOX. Material: Base em aço inox 304 e superior em Metalon galvanizado.<br><b>Custo R$ 9.000,00</b>",
    "Porta Guilhotina Pedra F": "Uma estrutura de aço inox de porta guilhotina, com contrapeso e  fechamento em pedra fornecida pelo cliente. Material: Base em aço inox 304 e superior em Metalon galvanizado.<br><b>Custo R$ 7.000,00</b>",
    "Coifa Epoxi": "Coifa interna para churrasqueira abrangendo a área de carvão, com 0 metros de dutos internos. Material:chapa galvanizada com pintura epóxi preta.<br><b>Custo R$ 3.200,00</b>",
    "Isolamento Coifa": "Isolamento térmico de coifa com manta de fibra cerâmica.<br><b>Custo R$ 800,00</b>",
    "Placa cimenticia Porta": "Aplicação de placa cimentícia sob porta guilhotina para fechamento e para receber o revestimento final.<br><b>Custo R$ 1.200,00</b>",
    "Revestimento Base": "Revestimento na base inferior da churrasqueira com placa cimentícia e manta de fibra cerâmica. (item recomendável para proteger marcenaria).<br><b>Custo R$ 1.500,00</b>",
    "Bifeteira grill": "Chapa bifeteira grill (adicional) para sistema de elevar.<br><b>Custo R$ 900,00</b>",
    "Balanço 2": "Regulagens de espetos em balanço 2 estágios. Material aço inox 304.<br><b>Custo R$ 450,00</b>",
    "Balanço 3": "Regulagens de espetos em balanço 3 estágios. Material aço inox 304.<br><b>Custo R$ 550,00</b>",
    "Balanço 4": "Regulagens de espetos em balanço 4 estágios. Material aço inox 304.<br><b>Custo R$ 650,00</b>",
    "Kit 6 Espetos": "Jogo de espetos 6 unidades sob medida com cabos em inox.<br><b>Custo R$ 750,00</b>",
    "Regulagem Comum 2": "Regulagem de espetos frente e fundo com 2 estágios. Material aço inox 304.<br><b>Custo R$ 350,00</b>",
    "Regulagem Comum 3": "Regulagem de espetos frente e fundo com 3 estágios. Material aço inox 304.<br><b>Custo R$ 450,00</b>",
    "Regulagem Comum 4": "Regulagem de espetos frente e fundo com 4 estágios. Material aço inox 304.<br><b>Custo R$ 550,00</b>",
    "Regulagem Comum 5": "Regulagem de espetos frente e fundo com 5 estágios. Material aço inox 304.<br><b>Custo R$ 650,00</b>",
    "Gavetão Inox": "Gavetão inferior a churrasqueira com corrediças e rodízios. Material: chapa galvanizada interno, e frontão em aço inox 304.<br><b>Custo R$ 2.800,00</b>",
    "Moldura Área de fogo": "Moldura área de fogo em aço inox 304. Material: aço inox 304.<br><b>Custo R$ 1.200,00</b>",
    "Grelha de descanso": "Grelha de descanso<br><b>Custo R$ 600,00</b>",
    "KAM800 2 Faces": "Lareira Kaminofen Modelo KAM800 DUPLA FACE com potência de 380m³. Material: Aço carbono 3mm com pintura preto alta temperatura, vidro cerâmico ShotRobax cordas de vedação do vidro e portas são importados.<br><b>Custo R$ 12.500,00</b>",
}

ITEM_DEFINITIONS_PRODUCAO = {
    "Tampa Inox": "Tampa aço inox 304.",
    "Tampa Epoxi": "Tampa chapa galvanizada pintura preta EPOXI.",
    "Revestimento Fundo": "Revestimento interno fundo aço inox 304.",
    "Revestimento Em L": "Revestimento interno fundo e uma lateral aço inox 304.",
    "Revestimento Em U": "Revestimento interno fundo e duas laterais aço inox 304.",
    "Sistema de Elevar Manual 2 3/16": "Sistema elevar grelhas MANUAL 2 grelhas vergalhão 3/16 aço inox 304.",
    "Sistema de Elevar Manual 1/8 e 3/16": "Sistema elevar grelhas MANUAL 2 grelhas vergalhão 3/16 e 1/8 aço inox 304.",
    "Sistema de Elevar Manual Arg e 3/16": "Sistema elevar grelhas MANUAL 2 grelhas vergalhão Arg e 3/16 aço inox 304.",
    "Sistema de Elevar Manual Arg e 1/8": "Sistema elevar grelhas MANUAL 2 grelhas vergalhão Arg e 1/8 aço inox 304.",
    "Sistema de Elevar Motor 2 3/16": "Sistema elevar grelhas elétrico 2 grelhas vergalhão 3/16 aço inox 304.",
    "Sistema de Elevar Motor 1/8 e 3/16": "Sistema elevar grelhas elétrico 2 grelhas vergalhão 1/8 e 3/16 aço inox 304.",
    "Sistema de Elevar Motor Arg e 3/16": "Sistema elevar grelhas elétrico 2 grelhas vergalhão Arg e 3/16 aço inox 304.",
    "Sistema de Elevar Motor Arg e 1/8": "Sistema elevar grelhas elétrico 2 grelhas vergalhão Arg e 1/8 aço inox 304.",
    "Giratório 1L 4E": "Sistema giratório 1 linha 4 espetos aço inox 304.",
    "Giratório 1L 5E": "Sistema giratório 1 linha 5 espetos aço inox 304.",
    "Giratório 2L 5E": "Sistema giratório 2 linhas 5 espetos aço inox 304.",
    "Giratório 2L 6E": "Sistema giratório 2 linhas 6 espetos aço inox 304.",
    "Giratório 2L 7E": "Sistema giratório 2 linhas 7 espetos aço inox 304.",
    "Giratório 2L 8E": "Sistema giratório 2 linhas 8 espetos aço inox 304.",
    "Cooktop + Bifeira": "Cooktop Tramontina tripla chama com Bifeira Grill 4mm aço inox 304.",
    "Cooktop": "Cooktop Tramontina tripla chama aço inox 304.",
    "Porta Guilhotina Vidro L": "Porta guilhotina vidro L aço inox 304 e Metalon galvanizado.",
    "Porta Guilhotina Vidro U": "Porta guilhotina vidro U aço inox 304 e Metalon galvanizado.",
    "Porta Guilhotina Vidro F": "Porta guilhotina vidro F aço inox 304 e Metalon galvanizado.",
    "Porta Guilhotina Inox F": "Porta guilhotina inox F aço inox 304 e Metalon galvanizado.",
    "Porta Guilhotina Pedra F": "Porta guilhotina pedra F aço inox 304 e Metalon galvanizado.",
    "Coifa Epoxi": "Coifa interna chapa galvanizada pintura epóxi preta.",
    "Isolamento Coifa": "Isolamento coifa manta de fibra cerâmica.",
    "Placa cimenticia Porta": "Placa cimentícia porta guilhotina.",
    "Revestimento Base": "Revestimento base inferior placa cimentícia e manta de fibra cerâmica.",
    "Bifeteira grill": "Bifeteira grill.",
    "Balanço 2": "Balanço 2 estágios aço inox 304.",
    "Balanço 3": "Balanço 3 estágios aço inox 304.",
    "Balanço 4": "Balanço 4 estágios aço inox 304.",
    "Kit 6 Espetos": "Kit 6 espetos.",
    "Regulagem Comum 2": "Regulagem comum 2 estágios aço inox 304.",
    "Regulagem Comum 3": "Regulagem comum 3 estágios aço inox 304.",
    "Regulagem Comum 4": "Regulagem comum 4 estágios aço inox 304.",
    "Regulagem Comum 5": "Regulagem comum 5 estágios aço inox 304.",
    "Gavetão Inox": "Gavetão inferior chapa galvanizada e aço inox 304.",
    "Moldura Área de fogo": "Moldura área de fogo aço inox 304.",
    "Grelha de descanso": "Grelha de descanso.",
    "KAM800 2 Faces": "Lareira Kaminofen KAM800 DUPLA FACE.",
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

DEFAULT_POSITIONS_PAGE2 = {
    "itemsStart": {"x": 42, "y": 780, "size": 12}, "lineHeight": 26
}

def load_positions(file_path, default_positions):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f: return json.load(f)
    return default_positions.copy()

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
        if tag in ['b', 'strong']: new_style['bold'] = True
        
        if tag == 'br':
            self.x = self.initial_x
            self.y -= self.wrapped_line_height
            
        attrs_dict = dict(attrs)
        if 'style' in attrs_dict:
            style_str = attrs_dict['style'].replace(' ', '').lower()
            if 'font-weight:bold' in style_str or 'font-weight:700' in style_str: new_style['bold'] = True
            if 'background-color:yellow' in style_str: new_style['highlight'] = True
        self.style_stack.append(new_style)

    def handle_endtag(self, tag):
        if len(self.style_stack) > 1: self.style_stack.pop()

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

def draw_wrapped_text(canvas, text, x, y, size, max_width):
    canvas.setFont("Helvetica", size)
    lines, words = [], text.split()
    if not words: return
    current_line = words[0]
    for word in words[1:]:
        if canvas.stringWidth(f"{current_line} {word}", "Helvetica", size) < max_width:
            current_line += f" {word}"
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    for i, line in enumerate(lines):
        canvas.drawString(x, y - (i * size * 1.2), line)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Lógica para obter o próximo número de orçamento
    query = orcamentos.select().with_only_columns(orcamentos.c.numero)
    all_numeros_records = await database.fetch_all(query)
    
    max_numero = 0
    if all_numeros_records:
        for record in all_numeros_records:
            try:
                # O registro pode ser um objeto RowProxy, acesse pelo nome da coluna
                numero_val = int(record.numero)
                if numero_val > max_numero:
                    max_numero = numero_val
            except (ValueError, TypeError, AttributeError):
                # Ignora valores que não são números inteiros ou registros malformados
                continue
    
    proximo_numero = max_numero + 1

    return templates.TemplateResponse("index.html", {
        "request": request, "positions": load_positions(POSITIONS_FILE, DEFAULT_POSITIONS),
        "today": date.today().isoformat(), "template_exists": get_template_path() is not None,
        "item_definitions": ITEM_DEFINITIONS,
        "item_definitions_producao": ITEM_DEFINITIONS_PRODUCAO,
        "proximo_numero": proximo_numero
    })

def get_template_path():
    if os.path.exists(TEMPLATE_UPLOAD_PATH): return TEMPLATE_UPLOAD_PATH
    if os.path.exists(TEMPLATE_PATH_DEFAULT): return TEMPLATE_PATH_DEFAULT
    return None

@app.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    with open(TEMPLATE_UPLOAD_PATH, "wb") as f: f.write(await file.read())
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    clean_filename = "".join(c for c in file.filename if c.isalnum() or c in (' ', '.', '_', '-')).strip()
    file_path = os.path.join(REFERENCIA_DIR, clean_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"filePath": f"/static/Referencia/{clean_filename}"}

@app.post("/save-positions")
async def api_save_positions(request: Request):
    data = await request.json()
    with open(POSITIONS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    return {"ok": True}

def draw_items_on_canvas(c, items_list, positions, page_width, initial_item_index=0, is_production=False):
    x_items = positions.get("itemsStart", {}).get("x", 42)
    y_items = positions.get("itemsStart", {}).get("y", 527)
    line_h = positions.get("lineHeight", 25)
    size = positions.get("itemsStart", {}).get("size", 12)
    y_cursor, numbered_item_index = y_items, initial_item_index

    for item_line in items_list:
        if y_cursor < 50:
            print("Aviso: Conteúdo excedeu o limite da página.")
            break

        # Lida com itens de imagem
        if item_line.startswith("@@IMAGE_START@@"):
            # Apenas desenha a imagem se NÃO for um orçamento de produção
            if not is_production:
                try:
                    image_data = item_line.replace("@@IMAGE_START@@", "").strip()
                    image_path, title = (image_data.split("|", 1) + ["Foto referência"])[:2]
                    full_image_path = os.path.join(APP_DIR, image_path.lstrip('/'))
                    if os.path.exists(full_image_path):
                        title_size = size - 1
                        c.setFont("Helvetica-Bold", title_size)
                        title_width = c.stringWidth(title, "Helvetica-Bold", title_size)
                        y_cursor -= (title_size * 1.5)
                        c.drawString((page_width - title_width) / 2, y_cursor, title)
                        y_cursor -= (line_h * 0.5)
                        img = Image.open(full_image_path)
                        aspect = img.height / float(img.width)
                        display_width = page_width * 0.45
                        display_height = display_width * aspect
                        y_cursor -= display_height
                        c.drawImage(full_image_path, (page_width - display_width) / 2, y_cursor, width=display_width, height=display_height, preserveAspectRatio=True)
                        y_cursor -= line_h
                except Exception as e:
                    print(f"Erro ao adicionar imagem {full_image_path}: {e}")
            # Pula para o próximo item da lista após tratar a imagem
            continue

        # Lida com itens de texto
        is_etapa = item_line.startswith("@@ETAPA_START@@")
        html_to_parse = item_line.replace("@@ETAPA_START@@", "").strip()
        
        if not is_etapa and is_production:
            item_key_search = re.sub('<[^<]+?>', '', html_to_parse).split('.')[0].strip()
            found_key = next((key for key, value in ITEM_DEFINITIONS.items() if item_key_search in value), None)
            if found_key:
                html_to_parse = ITEM_DEFINITIONS_PRODUCAO.get(found_key, html_to_parse)

        prefix_width = 0
        if not is_etapa:
            numbered_item_index += 1
            letter_prefix = f"{chr(64 + numbered_item_index)}) "
            c.setFont("Helvetica", size)
            c.drawString(x_items, y_cursor, letter_prefix)
            prefix_width = c.stringWidth(letter_prefix, "Helvetica", size)
            
        text_x = x_items + prefix_width
        max_x_items = page_width - x_items - 5
        parser = PDFHTMLParser(c, text_x, y_cursor, size, line_h, max_x_items, is_etapa=is_etapa)
        parser.feed(html_to_parse)

        y_cursor = parser.y - line_h

    return numbered_item_index

def generate_pdf_content(
    numero, data_formatada_pdf, responsavelObra, telefoneResponsavel, cliente, cpf,
    rg, enderecoObra, telefone, arquiteto, projeto, items, is_production=False
):
    template_path_p1 = get_template_path()
    if not template_path_p1:
        return None
    
    positions_p1 = load_positions(POSITIONS_FILE, DEFAULT_POSITIONS)
    
    all_pages_items = [page.strip() for page in items.split("@@PAGE_BREAK@@")]
    writer = PdfWriter()

    # --- Página 1 ---
    tpl_reader_p1 = PdfReader(template_path_p1)
    page_width, page_height = float(tpl_reader_p1.pages[0].mediabox.width), float(tpl_reader_p1.pages[0].mediabox.height)
    packet_p1 = io.BytesIO()
    c1 = canvas.Canvas(packet_p1, pagesize=(page_width, page_height))
    if p_num := positions_p1.get("numero"): c1.setFont("Helvetica-Bold", p_num.get("size", 10)); c1.drawString(p_num.get("x", 50), p_num.get("y", 750), str(numero))
    def draw_text_at(key, text):
        if p := positions_p1.get(key):
            if text:
                c1.setFont("Helvetica", p.get("size", 10))
                c1.drawString(p.get("x", 50), p.get("y", 750), str(text)[:200])
    draw_text_at("data", data_formatada_pdf); draw_text_at("responsavelObra", responsavelObra); draw_text_at("telefoneResponsavel", telefoneResponsavel)
    draw_text_at("cliente", cliente); draw_text_at("cpf", cpf); draw_text_at("rg", rg); draw_text_at("telefone", telefone)
    draw_text_at("arquiteto", arquiteto or "N/A"); draw_text_at("projeto", projeto or "N/A")
    if p_addr := positions_p1.get("enderecoObra"): draw_wrapped_text(c1, enderecoObra, p_addr.get("x", 60), p_addr.get("y", 660), p_addr.get("size", 10), page_width - p_addr.get("x", 60) - 25)
    
    items_list_p1 = [s.strip() for s in all_pages_items[0].splitlines() if s.strip()]
    last_item_index = draw_items_on_canvas(c1, items_list_p1, positions_p1, page_width, 0, is_production)
    
    c1.save(); packet_p1.seek(0)
    tpl_page_p1 = tpl_reader_p1.pages[0]; tpl_page_p1.merge_page(PdfReader(packet_p1).pages[0]); writer.add_page(tpl_page_p1)
    for i in range(1, len(tpl_reader_p1.pages)): writer.add_page(tpl_reader_p1.pages[i])

    # --- Páginas Adicionais (2, 3, 4, etc.) ---
    if len(all_pages_items) > 1 and os.path.exists(TEMPLATE_PATH_PAGE2):
        positions_p2 = load_positions(POSITIONS_FILE_PAGE2, DEFAULT_POSITIONS_PAGE2)
        
        for page_items_str in all_pages_items[1:]:
            items_list_p_n = [s.strip() for s in page_items_str.splitlines() if s.strip()]
            if not items_list_p_n: continue

            tpl_reader_p2 = PdfReader(TEMPLATE_PATH_PAGE2)
            tpl_page_p_n = tpl_reader_p2.pages[0]
            page_width_p2, page_height_p2 = float(tpl_page_p_n.mediabox.width), float(tpl_page_p_n.mediabox.height)

            packet_p_n = io.BytesIO()
            c_n = canvas.Canvas(packet_p_n, pagesize=(page_width_p2, page_height_p2))
            
            last_item_index = draw_items_on_canvas(c_n, items_list_p_n, positions_p2, page_width_p2, last_item_index, is_production)
            c_n.save(); packet_p_n.seek(0)
            
            overlay_page = PdfReader(packet_p_n).pages[0]
            tpl_page_p_n.merge_page(overlay_page)
            writer.add_page(tpl_page_p_n)

    out_bytes = io.BytesIO(); writer.write(out_bytes); out_bytes.seek(0)
    return out_bytes

@app.post("/generate")
async def generate_pdf_for_preview(
    numero: str = Form(""), data: str = Form(""), responsavelObra: str = Form(""),
    telefoneResponsavel: str = Form(""), cliente: str = Form(""), cpf: str = Form(""),
    rg: str = Form(""), enderecoObra: str = Form(""), telefone: str = Form(""),
    arquiteto: str = Form(""), projeto: str = Form(""), items: str = Form(""),
    mode: str = Form("cliente")
):
    data_formatada_pdf = data
    try: data_formatada_pdf = datetime.strptime(data, '%Y-%m-%d').strftime("%d de %B de %Y").replace(" de 0", " de ")
    except ValueError: pass
    
    is_production = (mode == "producao")
    
    pdf_bytes = generate_pdf_content(
        numero, data_formatada_pdf, responsavelObra, telefoneResponsavel, cliente, cpf,
        rg, enderecoObra, telefone, arquiteto, projeto, items, is_production=is_production
    )
    
    if not pdf_bytes:
        return HTMLResponse("Nenhum template de orçamento disponível.", status_code=400)
    
    return StreamingResponse(pdf_bytes, media_type="application/pdf")

@app.post("/generate-pdfs")
async def generate_both_pdfs(
    numero: str = Form(""), data: str = Form(""), responsavelObra: str = Form(""),
    telefoneResponsavel: str = Form(""), cliente: str = Form(""), cpf: str = Form(""),
    rg: str = Form(""), enderecoObra: str = Form(""), telefone: str = Form(""),
    arquiteto: str = Form(""), projeto: str = Form(""),
    items_cliente: str = Form(""),
    items_producao: str = Form("")
):
    data_formatada_pdf = data
    try:
        data_formatada_pdf = datetime.strptime(data, '%Y-%m-%d').strftime("%d de %B de %Y").replace(" de 0", " de ")
    except ValueError:
        pass
    
    # Generate Cliente PDF
    args_cliente = (numero, data_formatada_pdf, responsavelObra, telefoneResponsavel, cliente, cpf, rg, enderecoObra, telefone, arquiteto, projeto, items_cliente)
    pdf_cliente_bytes = generate_pdf_content(*args_cliente, is_production=False)
    
    # Generate Producao PDF
    args_producao = (numero, data_formatada_pdf, responsavelObra, telefoneResponsavel, cliente, cpf, rg, enderecoObra, telefone, arquiteto, projeto, items_producao)
    pdf_producao_bytes = generate_pdf_content(*args_producao, is_production=True)

    if not pdf_cliente_bytes or not pdf_producao_bytes:
        return JSONResponse({"error": "Nenhum template de orçamento disponível."}, status_code=400)

    pdf_cliente_b64 = base64.b64encode(pdf_cliente_bytes.getvalue()).decode('utf-8')
    pdf_producao_b64 = base64.b64encode(pdf_producao_bytes.getvalue()).decode('utf-8')

    clean_cliente_name = "".join(c for c in cliente if c.isalnum() or c in (' ')).strip()
    filename_cliente = f"Orçamento {numero} {clean_cliente_name}.pdf"
    filename_producao = f"Orçamento {numero} {clean_cliente_name} Produção.pdf"

    return JSONResponse({
        "cliente": pdf_cliente_b64,
        "producao": pdf_producao_b64,
        "filename_cliente": filename_cliente,
        "filename_producao": filename_producao
    })

@app.post("/orcamentos")
async def save_orcamento(request: Request):
    form_data = await request.form()
    orcamento_data = dict(form_data)
    
    query = orcamentos.select().where(orcamentos.c.numero == orcamento_data["numero"])
    existing_orcamento = await database.fetch_one(query)

    if existing_orcamento:
        update_query = orcamentos.update().where(orcamentos.c.numero == orcamento_data["numero"]).values(
            cliente=orcamento_data["cliente"],
            data_atualizacao=datetime.now().isoformat(),
            dados=orcamento_data
        )
        await database.execute(update_query)
        return {"status": "updated"}
    else:
        insert_query = orcamentos.insert().values(
            numero=orcamento_data["numero"],
            cliente=orcamento_data["cliente"],
            data_atualizacao=datetime.now().isoformat(),
            dados=orcamento_data
        )
        await database.execute(insert_query)
        return {"status": "created"}

@app.get("/orcamentos")
async def get_orcamentos():
    query = orcamentos.select()
    results = await database.fetch_all(query)
    return [dict(result) for result in results]

@app.get("/orcamentos/{orcamento_id}")
async def get_orcamento(orcamento_id: int):
    query = orcamentos.select().where(orcamentos.c.id == orcamento_id)
    orcamento = await database.fetch_one(query)
    if orcamento is None:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    return orcamento

@app.delete("/orcamentos/{orcamento_id}")
async def delete_orcamento(orcamento_id: int):
    query = orcamentos.delete().where(orcamentos.c.id == orcamento_id)
    await database.execute(query)
    return {"status": "deleted"}
