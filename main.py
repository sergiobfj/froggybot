import telebot, json, requests, gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from time import sleep
from datetime import datetime

#Carregando o JSON com algumas informações 
with open("creds.json", "r") as file:
    creds = json.load(file)
    
creds['api_sheets']['private_key'] = creds['api_sheets']['private_key'].replace('\\n', '\n')

# Usando o método nativo do gspread para autorização a partir do dicionário.
gc = gspread.service_account_from_dict(creds['api_sheets'])
# =================================================================

#Atribuindo as informações do JSON a variáveis
bot = telebot.TeleBot(creds['telegram']['bot_token'])
sheet_url = creds['planilha']
shortner_url = creds['encurtador']
chat_id = creds['telegram']['chat_id_prod']

sheet = gc.open_by_url(sheet_url)  # seu link da planilha
worksheet = sheet.sheet1
df = pd.DataFrame(worksheet.get_all_records())

print(f"[FROGGY-LOG] Iniciando as atividades! - {datetime.now()}")
print('-=' * 30)

#Lembrar de enviar alguns exemplos de frase nos primeiros posts de cada dia. Ou também 
#Algumas frases de efeito antes do primeiro post em cada TURNO do dia.
bot.send_message(chat_id, "Fala pessoal! Promoções novas hoje!")

#Lembrando, a mensagem acompanha a identação, ou seja, caso deixe a mensagem indentada em python,
#irá aplicar os "espaços vazios" também na exibição.

def envioUnico():
    global df, worksheet

    # Descobre o índice da coluna STATUS
    status_col_index = df.columns.get_loc("STATUS") + 1  # +1 porque gspread começa em 1
    # Filtra apenas as linhas que não estão "ENVIADO"
    df_to_send = df[df['STATUS'] != "ENVIADO"]

    if df_to_send.empty:
        print("[FROGGY-LOG] Nenhum produto para enviar.")
        return

    # Pega a primeira linha que precisa enviar
    i = df_to_send.index[0]
    product = df.loc[i].to_dict()

    # Encurtador de URL
    body = {"url": product['LINK']}
    product_url = requests.post(shortner_url, json=body).json()
    
    print(product_url["urlEncurtada"])
    print(f"[FROGGY-LOG] PRODUTO ENVIADO! ID: {i} | NOME: {product['NOME']} | - {datetime.now()}")

    # Mensagem
    mensagem = f""" 
{product['FRASE']} 🐸

<b>{product['NOME']}</b>

De: <s>{product['VALOR_ANTIGO']}</s>            

<b>Por: {product['VALOR_PROMO']} 😍</b>
<i>CUPOM: {product['CUPOM']} ✨</i>​

Compre aqui:
🛍️ {product["LINK"]}
"""
    # Envia foto
    bot.send_photo(chat_id, photo=product["IMAGEM"], caption=mensagem, parse_mode="HTML")
    print('-=' * 30)

    # Atualiza STATUS na planilha
    worksheet.update_cell(i + 2, status_col_index, "ENVIADO")  # +2 por causa do cabeçalho
    print(f"[FROGGY-LOG] STATUS atualizado para ENVIADO na linha {i+2}")

def envioEmLote():
    for i in range(len(df)):
        product = df.iloc[i].to_dict()
        print(f"Produto: {product['NOME']} | Preço: {product['VALOR_PROMO']}")
        print(f"Produto: {product['NOME']} | Preço: {product['VALOR_PROMO']}")
        
        bot.send_message(
            chat_id, 
            f"""
            OFERTAS DO SAPO LOUCO 🐸
            {product['FRASE']}

            {product['NOME']}

            De: ~~{product['VALOR_ANTIGO']}~~            
            Por: {product['VALOR_PROMO']} 😍
            CUPOM: {product['CUPOM']} ✨​

            Compre aqui:
            🛍️ {product['LINK']}

            """, parse_mode="HTML")
        print('-=' * 30)

#Executando o código de acordo com o fluxo
envioUnico()
print(f"[FROGGY-LOG] Finalizando envio! - {datetime.now()}")
print(f"[FROGGY-LOG] Aguardando horário...")
