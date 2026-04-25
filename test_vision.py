"""
Test script: reads the first page of a PDF as an image and sends it to llama3.2-vision.
Run: python test_vision.py
"""

import base64
import json
import urllib.request
from pdf2image import convert_from_path

PDF_PATH     = "documents/personal/2026-04-22_2023_consolidato_annuale_svilapp.pdf"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
MODEL        = "llama3.2-vision:11b"
OLLAMA_URL   = "http://localhost:11434/api/generate"

# Convert first page to image
print("Converting first page to image...")
pages = convert_from_path(PDF_PATH, first_page=1, last_page=1, dpi=200, poppler_path=POPPLER_PATH)
pages[0].save("data/test_page.jpg", "JPEG")

with open("data/test_page.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Send via raw HTTP
print(f"Sending to {MODEL}...")
payload = json.dumps({
    "model": MODEL,
    "prompt": """This is a page from an Italian payslip (busta paga).
Extract all the following information:
- Employee name
- Month and year
- Gross salary (retribuzione lorda)
- Net salary (retribuzione netta)
- INPS contributions
- IRPEF tax
- Any other monetary values

List each item clearly.""",
    "images": [img_b64],
    "stream": False,
}).encode("utf-8")

req = urllib.request.Request(
    OLLAMA_URL,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=300) as resp:
    result = json.loads(resp.read().decode("utf-8"))

print(f"\n=== {MODEL} Response ===")
print(result.get("response", "No response"))