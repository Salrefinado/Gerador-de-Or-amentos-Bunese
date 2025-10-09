python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# coloque Orçamento 2.0.pdf na raiz do projeto (ou use a interface para fazer upload)
uvicorn main:app --reload
# abra http://127.0.0.1:8000
