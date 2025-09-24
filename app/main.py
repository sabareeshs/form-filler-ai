from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
import requests
import tempfile
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import time

app = FastAPI()

# Hugging Face API settings
HF_API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
HF_TOKEN = os.getenv("HF_TOKEN")  # Set this as environment variable

def query_huggingface(question: str, context: str, max_retries=3):
    """Query Hugging Face Inference API with retries"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    
    payload = {
        "inputs": {
            "question": question,
            "context": context
        }
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 503:
                # Model is loading, wait and retry
                print(f"Model loading, waiting 20 seconds... (attempt {attempt + 1})")
                time.sleep(20)
                continue
            elif response.status_code == 429:
                # Rate limited, wait and retry
                print(f"Rate limited, waiting 10 seconds... (attempt {attempt + 1})")
                time.sleep(10)
                continue
            elif response.status_code == 200:
                result = response.json()
                return result.get("answer", "")
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            print(f"Request timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
        except Exception as e:
            print(f"Error querying Hugging Face API: {e}")
            return ""
    
    return ""

def extract_text_from_pdf_bytes(pdf_bytes: bytes):
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join([page.get_text() for page in pdf])
    pdf.close()
    return text

def extract_questions(pdf_bytes: bytes):
    text = extract_text_from_pdf_bytes(pdf_bytes)
    lines = text.splitlines()
    questions = [line.strip() for line in lines if "?" in line and len(line.strip()) > 5]
    return questions

def answer_questions(questions, context):
    """Answer questions using Hugging Face Inference API"""
    qa_pairs = []
    
    # Truncate context if too long (HF API has limits)
    if len(context) > 4000:
        context = context[:4000] + "..."
    
    for i, q in enumerate(questions):
        print(f"Processing question {i+1}/{len(questions)}: {q[:50]}...")
        
        # Clean up question
        q = q.strip()
        if not q:
            continue
            
        answer = query_huggingface(q, context)
        qa_pairs.append((q, answer if answer else "Unable to find answer"))
        
        # Add small delay to avoid rate limiting
        time.sleep(1)
    
    return qa_pairs

def generate_filled_pdf(qa_pairs, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50
    
    for q, a in qa_pairs:
        # Handle long text by wrapping
        q_lines = [q[i:i+80] for i in range(0, len(q), 80)]
        a_lines = [a[i:i+80] for i in range(0, len(a), 80)]
        
        # Draw question
        c.drawString(30, y, f"Q: {q_lines[0]}")
        y -= 15
        for line in q_lines[1:]:
            c.drawString(50, y, line)
            y -= 15
        
        # Draw answer
        c.drawString(30, y, f"A: {a_lines[0]}")
        y -= 15
        for line in a_lines[1:]:
            c.drawString(50, y, line)
            y -= 15
        
        y -= 20  # Extra space between Q&A pairs
        
        # New page if needed
        if y < 100:
            c.showPage()
            y = height - 50
    
    c.save()

@app.get("/", response_class=HTMLResponse)
def upload_form():
    html = """
    <html>
    <head>
        <title>PDF Form Filler - HF API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; }
            input[type="file"] { margin: 10px 0; padding: 5px; }
            input[type="submit"] { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
      <div class="container">
        <h2>PDF Form Filler (Hugging Face API)</h2>
        
        <div class="info">
          <strong>Instructions:</strong>
          <ul>
            <li>Upload a PDF with questions (lines containing "?")</li>
            <li>Upload a PDF with data/context to answer from</li>
            <li>Get a filled PDF with AI-generated answers</li>
          </ul>
        </div>
        
        <form action="/fill-form" enctype="multipart/form-data" method="post">
          <label><strong>Questions PDF:</strong><br/>
          <input type="file" name="questions_pdf" accept=".pdf" required /></label><br/>
          
          <label><strong>Data PDF:</strong><br/>
          <input type="file" name="data_pdf" accept=".pdf" required /></label><br/>
          
          <input type="submit" value="Fill Form"/>
        </form>
        
        <p><small>Note: Processing may take 1-2 minutes depending on the number of questions.</small></p>
      </div>
    </body>
    </html>
    """
    return html

@app.post("/fill-form")
async def fill_form(questions_pdf: UploadFile = File(...), data_pdf: UploadFile = File(...)):
    try:
        print("Reading uploaded files...")
        questions_bytes = await questions_pdf.read()
        data_bytes = await data_pdf.read()
        
        print("Extracting questions...")
        questions = extract_questions(questions_bytes)
        print(f"Found {len(questions)} questions")
        
        if not questions:
            return HTMLResponse(
                "<h3>Error: No questions found in the PDF. Make sure questions end with '?'</h3>"
                "<a href='/'>Try again</a>",
                status_code=400
            )
        
        print("Extracting context...")
        context = extract_text_from_pdf_bytes(data_bytes)
        
        if len(context) < 50:
            return HTMLResponse(
                "<h3>Error: Not enough context found in the data PDF.</h3>"
                "<a href='/'>Try again</a>",
                status_code=400
            )
        
        print("Processing with AI...")
        qa_pairs = answer_questions(questions, context)

        print("Generating PDF...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            output_path = tmp.name
        
        generate_filled_pdf(qa_pairs, output_path)
        
        return FileResponse(
            output_path, 
            filename="filled_form.pdf", 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=filled_form.pdf"}
        )
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return HTMLResponse(
            f"<h3>Error processing your request: {str(e)}</h3>"
            "<a href='/'>Try again</a>",
            status_code=500
        )

@app.get("/health")
def health_check():
    return {"status": "healthy", "using": "Hugging Face Inference API"}
