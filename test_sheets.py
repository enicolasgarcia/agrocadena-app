import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)

sheet = client.open("NOMBRE_DE_TU_SHEET").sheet1

sheet.append_row(["Finca 1", 100, 5000])

print("Datos guardados en Google Sheets ✅")
