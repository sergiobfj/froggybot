import telebot, json, requests, gspread, os # Adicione 'os' para ler variáveis de ambiente
from google.oauth2.service_account import Credentials
import pandas as pd
from time import sleep
from datetime import datetime

# --- INÍCIO DAS MODIFICAÇÕES ---

# Passo 1: Carregar as credenciais do Google a partir da variável de ambiente
# Em vez de ler de um arquivo, lemos a string JSON da variável de ambiente.
google_creds_str = os.environ.get('GOOGLE_SHEETS_CREDS_JSON')

# Verificação para garantir que a variável foi carregada
if not google_creds_str:
    raise ValueError("A variável de ambiente 'GOOGLE_SHEETS_CREDS_JSON' não foi encontrada!")

# A biblioteca do Google precisa de um dicionário, então convertemos a string JSON.
creds_dict = json.loads(google_creds_str)

# Passo 2: Corrigir a 'private_key'
# O Railway pode escapar as quebras de linha ('\n' vira '\\n').
# Esta linha garante que a chave privada tenha o formato correto.
creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')

# Passo 3: Carregar as outras variáveis de ambiente
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')
sheet_url = os.environ.get('SHEET_URL')
shortner_url = os.environ.get('SHORTNER_URL')

# Verificações para as outras variáveis
if not all([bot_token, chat_id, sheet_url, shortner_url]):
    raise ValueError("Uma ou mais variáveis de ambiente (TELEGRAM_BOT_TOKEN, CHAT_ID, etc.) não foram definidas!")

# --- FIM DAS MODIFICAÇÕES ---


# Agora, o resto do seu código usa as variáveis que carregamos do ambiente
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
# Usamos o dicionário corrigido para autenticar
creds_sheets = Credentials.from_service_account_info(creds_dict, scopes=scopes )
gc = gspread.authorize(creds_sheets)

#Atribuindo as informações do ambiente a variáveis
bot = telebot.TeleBot(bot_token)

sheet = gc.open_by_url(sheet_url)
worksheet = sheet.sheet1
df = pd.DataFrame(worksheet.get_all_records())


print(f"[FROGGY-LOG] Iniciando as atividades! - {datetime.now()}")
print('-=' * 30)

bot.send_message(chat_id, "Fala pessoal! Promoções novas hoje!")

def envioUnico():
    global df, worksheet

    status_col_index = df.columns.get_loc("STATUS") + 1
    df_to_send = df[df['STATUS'] != "ENVIADO"]

    if df_to_send.empty:
        print("[FROGGY-LOG] Nenhum produto para enviar.")
        return

    i = df_to_send.index[0]
    product = df.loc[i].to_dict()

    body = {"url": product['LINK']}
    response = requests.post(shortner_url, json=body)
    response.raise_for_status() # Adicionado para verificar erros na API do encurtador
    product_url = response.json()
    
    # A chave no JSON de resposta pode ser 'urlEncurtada' ou outra, ajuste se necessário
    short_url = product_url.get("urlEncurtada", product['LINK']) 
    
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

# A função envioEmLote não estava sendo chamada, mantive-a caso você a use no futuro.
def envioEmLote():
    # ... (seu código aqui)
    pass

#Executando o código de acordo com o fluxo
envioUnico()
print(f"[FROGGY-LOG] Finalizando envio! - {datetime.now()}")
print(f"[FROGGY-LOG] Aguardando horário...")

