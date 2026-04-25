"""
Test script: reads the first page of a PDF as an image and sends it to GLM-OCR.
Run: python test_llava.py
"""

import base64
import ollama
from pdf2image import convert_from_path

PDF_PATH     = "documents/personal/2026-04-22_2023_consolidato_annuale_svilapp.pdf"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
MODEL        = "glm-ocr"

# Convert first page to image
print("Converting first page to image...")
pages = convert_from_path(PDF_PATH, first_page=1, last_page=1, dpi=200, poppler_path=POPPLER_PATH)
page  = pages[0]

# Save and encode to base64
img_path = "data/test_page.jpg"
page.save(img_path, "JPEG")
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Ask GLM-OCR to extract data
print(f"Sending to {MODEL}...")
client = ollama.Client(timeout=120)

response = client.generate(
    model=MODEL,
    prompt="""This is a page from an Italian payslip (busta paga).
Extract all the following information:
- Employee name
- Month and year
- Gross salary (retribuzione lorda)
- Net salary (retribuzione netta)
- INPS contributions
- IRPEF tax
- Any other monetary values

List each item clearly.""",
    images=[img_b64],
)

print(f"\n=== {MODEL} Response ===")
print(response["response"])