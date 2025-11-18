import pandas as pd
from openpyxl import Workbook

def save_to_excel(data, file_path ="invoices.xlsx"):

    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return file_path