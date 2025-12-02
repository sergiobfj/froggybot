import telebot, json, requests, gspread, os
from google.oauth2.service_account import Credentials
import pandas as pd
from time import sleep
from datetime import datetime

# --- INÍCIO DA SEÇÃO DE CONFIGURAÇÃO ---

# Constrói o dicionário de credenciais do Google a partir de variáveis de ambiente individuais.
# Isso evita qualquer problema de formatação de JSON.
try:
    creds_dict = {
        "type": os.environ['TYPE'],
        "project_id": os.environ['PROJECT_ID'],
        "private_key_id": os.environ['PRIVATE_KEY_ID'],
        # A linha abaixo é a correção crucial: garante que as quebras de linha da chave privada sejam interpretadas corretamente.
        "private_key": os.environ['PRIVATE_KEY'].replace('\\n', '\n'),
        "client_email": os.environ['CLIENT_EMAIL'],
        "client_id": os.environ['CLIENT_ID'],
        "auth_uri": os.environ['AUTH_URI'],
        "token_uri": os.environ['TOKEN_URI'],
        "auth_provider_x509_cert_url": os.environ['AUTH_PROVIDER_X509_CERT_URL'],
        "client_x509_cert_url": os.environ['CLIENT_X509_CERT_URL']
    }
except KeyError as e:
    print(f"[FROGGY-LOG] ERRO CRÍTICO: A variável de ambiente {e} não foi encontrada!")
    raise

# Carrega as outras configurações do ambiente
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')
sheet_url = os.environ.get('SHEET_URL')
shortner_url = os.environ.get('SHORTNER_URL')

if not all([bot_token, chat_id, sheet_url, shortner_url]):
    raise ValueError("ERRO: Uma ou mais variáveis (TELEGRAM_BOT_TOKEN, CHAT_ID, etc.) não foram definidas!")

# --- FIM DA SEÇÃO DE CONFIGURAÇÃO ---


# Autenticação e inicialização dos serviços
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds_sheets = Credentials.from_service_account_info(creds_dict, scopes=scopes )
gc = gspread.authorize(creds_sheets)

bot = telebot.TeleBot(bot_token)
sheet = gc.open_by_url(sheet_url)
worksheet = sheet.sheet1
df = pd.DataFrame(worksheet.get_all_records())


print(f"[FROGGY-LOG] Iniciando as atividades! - {datetime.now()}")
print('-=' * 30)

bot.send_message(chat_id, "Fala pessoal! Promoções novas hoje!")

def envioUnico():
    global df, worksheet

    if df.empty or "STATUS" not in df.columns:
        print("[FROGGY-LOG] DataFrame está vazio ou não contém a coluna 'STATUS'.")
        return

    status_col_index = df.columns.get_loc("STATUS") + 1
    df_to_send = df[df['STATUS'] != "ENVIADO"]

    if df_to_send.empty:
        print("[FROGGY-LOG] Nenhum produto novo para enviar.")
        return

    i = df_to_send.index[0]
    product = df.loc[i].to_dict()

    try:
        body = {"url": product['LINK']}
        response = requests.post(shortner_url, json=body)
        response.raise_for_status()
        product_url = response.json()
        short_url = product_url.get("urlEncurtada", product['LINK'])
    except requests.exceptions.RequestException as e:
        print(f"[FROGGY-LOG] Erro ao encurtar URL: {e}. Usando link original.")
        short_url = product['LINK']
    
    print(f"[FROGGY-LOG] PRODUTO ENVIADO! ID: {i} | NOME: {product['NOME']} | - {datetime.now()}")

    mensagem = f""" 
{product['FRASE']} 🐸

<b>{product['NOME']}</b>

De: <s>{product['VALOR_ANTIGO']}</s>            

<b>Por: {product['VALOR_PROMO']} 😍</b>
<i>CUPOM: {product['CUPOM']} ✨</i>​

Compre aqui:
🛍️ {short_url}
"""
    bot.send_photo(chat_id, photo=product["IMAGEM"], caption=mensagem, parse_mode="HTML")
    print('-=' * 30)

    worksheet.update_cell(i + 2, status_col_index, "ENVIADO")
    print(f"[FROGGY-LOG] STATUS atualizado para ENVIADO na linha {i+2}")

# Execução
envioUnico()
print(f"[FROGGY-LOG] Finalizando envio! - {datetime.now()}")
print(f"[FROGGY-LOG] Aguardando horário...")
