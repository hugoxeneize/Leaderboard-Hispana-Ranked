import requests
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === CONFIGURACIÓN ===

pais_nombres = {
    'ar': 'Argentina', 'bo': 'Bolivia', 'cl': 'Chile', 'co': 'Colombia', 'cr': 'Costa Rica',
    'cu': 'Cuba', 'do': 'República Dominicana', 'ec': 'Ecuador', 'gt': 'Guatemala', 'hn': 'Honduras',
    'mx': 'México', 'ni': 'Nicaragua', 'pa': 'Panamá', 'py': 'Paraguay', 'pe': 'Perú',
    'pr': 'Puerto Rico', 'sv': 'El Salvador', 'uy': 'Uruguay', 've': 'Venezuela', 'es': 'España', 'gq': 'Guinea Ecuatorial'
}

def emoji_bandera(iso):
    if not isinstance(iso, str) or pd.isna(iso):
        return ''
    OFFSET = 127397
    return ''.join([chr(ord(c.upper()) + OFFSET) for c in iso])

# === CONSULTA A API ===

url_base = "https://mcsrranked.com/api/leaderboard"
hispano_paises = list(pais_nombres.keys())
jugadores = []
errores = []

for codigo_pais in hispano_paises:
    print(f"Consultando {codigo_pais}...")
    try:
        r = requests.get(url_base, params={"country": codigo_pais})
        if r.status_code == 200:
            respuesta = r.json()
            users = respuesta.get("data", {}).get("users", [])
            for jugador in users:
                jugador["country"] = codigo_pais
                jugador["elo"] = jugador.get("eloRate", None)
                jugadores.append(jugador)
        else:
            errores.append((codigo_pais, r.status_code))
    except Exception as e:
        errores.append((codigo_pais, str(e)))

# === PROCESAMIENTO DE DATOS ===

df = pd.DataFrame(jugadores)
print(f"\nJugadores encontrados: {len(df)}")

if not df.empty:
    df.rename(columns={'eloRank': 'Global', 'country': 'País', 'nickname': 'Nickname'}, inplace=True)

    df['elo'] = df['elo'].astype(float)
    df = df.sort_values(by='elo', ascending=False).reset_index(drop=True)
    df['Top'] = df.index + 1

    # Agregar código ISO y emoji de bandera
    df['iso'] = df['País']
    df['Emoji'] = df['iso'].apply(emoji_bandera)

    # Reemplazar país por emoji únicamente
    df['País'] = df['Emoji']

    # Orden final
    df = df[['Top', 'Global', 'País', 'Nickname', 'elo']]

    # === ACTUALIZAR GOOGLE SHEETS ===

    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/hugoxeneize/aPROYECTOSPY/hispanoslb/code/credenciales.json', SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Leaderboard Hispana Ranked")
    sheet = spreadsheet.sheet1

    # Limpiar columnas A a E y preparar hoja
    sheet.batch_clear(['A1:E1000'])
    sheet.resize(rows=len(df) + 10, cols=6)
    sheet.freeze(rows=1)

    # Insertar tabla
    set_with_dataframe(sheet, df)

    # Hora de actualización en F2
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    sheet.update('F2', [[f"Última actualización:\n{ahora}"]])
    sheet.format('F2', {
        "wrapStrategy": "WRAP",
        "textFormat": {"fontSize": 10, "italic": True}
    })

    # Colores por rango de ELO
    colores = {
        "coal":     {"backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}},
        "iron":     {"backgroundColor": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "gold":     {"backgroundColor": {"red": 1.0, "green": 0.84, "blue": 0.0}},
        "emerald":  {"backgroundColor": {"red": 0.0, "green": 1.0, "blue": 0.6}},
        "diamond":  {"backgroundColor": {"red": 0.6, "green": 0.9, "blue": 1.0}},
        "netherite":{"backgroundColor": {"red": 0.2, "green": 0.1, "blue": 0.1}},
    }

    # Agrupar filas por rango de ELO para aplicar formato en batch
    rangos_filas = {
        "coal": [],
        "iron": [],
        "gold": [],
        "emerald": [],
        "diamond": [],
        "netherite": []
    }

    for i, elo in enumerate(df['elo'], start=2):
        if elo < 600:
            rangos_filas['coal'].append(i)
        elif elo < 900:
            rangos_filas['iron'].append(i)
        elif elo < 1200:
            rangos_filas['gold'].append(i)
        elif elo < 1500:
            rangos_filas['emerald'].append(i)
        elif elo < 2000:
            rangos_filas['diamond'].append(i)
        else:
            rangos_filas['netherite'].append(i)

    for rango, filas in rangos_filas.items():
        if filas:
            start = min(filas)
            end = max(filas)
            sheet.format(f'A{start}:E{end}', colores[rango])

    print("\n✅ Leaderboard actualizado exitosamente en Google Sheets.")
else:
    print("\n⚠️ No se encontraron datos para generar el leaderboard.")

