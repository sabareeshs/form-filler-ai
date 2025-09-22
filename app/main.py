from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from transformers import pipeline
import tempfile
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = FastAPI()

# QA model (change to lighter model if needed)
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

def extract_text_from_pdf_bytes(pdf_bytes: bytes):
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join([page.get_text() for page in pdf])
    pdf.close()
    return text

def extract_questions(pdf_bytes: bytes):
    text = extract_text_from_pdf_bytes(pdf_bytes)
    lines = text.splitlines()
    questions = [line.strip() for line in lines if "?" in line]
    return questions

def answer_questions(questions, context):
    qa_pairs = []
    for q in questions:
        try:
            result = qa_pipeline(question=q, context=context)
            answer = result.get('answer', '')
        except Exception as e:
            answer = ""
        qa_pairs.append((q, answer))
    return qa_pairs

def generate_filled_pdf(qa_pairs, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50
    for q, a in qa_pairs:
        c.drawString(30, y, f"Q: {q}")
        y -= 20
        c.drawString(50, y, f"A: {a}")
        y -= 30
        if y < 100:
            c.showPage()
            y = height - 50
    c.save()

@app.get("/", response_class=HTMLResponse)
def upload_form():
    html = """
    <html>
    <body>
      <h2>PDF Form Filler</h2>
      <form action="/fill-form" enctype="multipart/form-data" method="post">
        <label>Questions PDF: <input type="file" name="questions_pdf" /></label><br/><br/>
        <label>Data PDF: <input type="file" name="data_pdf" /></label><br/><br/>
        <input type="submit" value="Fill Form"/>
      </form>
    </body>
    </html>
    """
    return html

@app.post("/fill-form")
async def fill_form(questions_pdf: UploadFile = File(...), data_pdf: UploadFile = File(...)):
    questions_bytes = await questions_pdf.read()
    data_bytes = await data_pdf.read()
    questions = extract_questions(questions_bytes)
    context = extract_text_from_pdf_bytes(data_bytes)
    qa_pairs = answer_questions(questions, context)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name
    generate_filled_pdf(qa_pairs, output_path)

    return FileResponse(output_path, filename="filled_form.pdf", media_type="application/pdf")

