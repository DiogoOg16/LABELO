import pandas as pd
import pdfplumber
import os
import re

#print(pd.__version__)
#print(pdfplumber.__version__)



USER_PATH = r"C:\Users\80403185\Documents\Codigos"
PDF_PATH = r"\doc\doc1.pdf"

PATH = USER_PATH + PDF_PATH

data = []

with pdfplumber.open(PATH) as pdf:
    #for page in pdf.pages:
     page = pdf.pages[1]
     #extract lines
     text = page.extract_text()
     print(text)   

for data in page:
     