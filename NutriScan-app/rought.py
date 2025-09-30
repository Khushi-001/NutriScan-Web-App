""""
import pytesseract
print(pytesseract.get_tesseract_version())


# Explicit path to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
################
from PIL import Image
import pytesseract

# Test with a simple image or check if tesseract is accessible
print("Tesseract path:", pytesseract.pytesseract.tesseract_cmd)
"""
from flask import Flask
import pytesseract
from PIL import Image

app = Flask(__name__)

# Your tesseract path that works
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.route('/')
def hello():
    return "Flask is working!"

if __name__ == '__main__':
    app.run(debug=True)