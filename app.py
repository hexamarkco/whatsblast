from tkinter import filedialog
from datetime import datetime
from itertools import cycle
import tkinter as tk
import requests
import hashlib
import random
import time
import csv
import os

pasta_raiz = os.path.dirname(os.path.abspath(__file__))
arquivo_status = os.path.join(pasta_raiz, 'status_envio.csv')

CAMINHO_ARQUIVO_LOG = None
INSTANCIA = "3C2023FF0C9C008C2EC24AFC3B724725"
TOKEN = "F180E43C90FCA97781F8E6D4"
HEADERS = {
    "content-type": "application/json",
    "Client-Token": "Ff0748c74a332451096a886ebc80c40a7S"
}

BASE_URL = f"https://api.z-api.io/instances/{INSTANCIA}/token/{TOKEN}"

botao_lista = [
    {"id": "1", "label": "Quero saber mais!"},
    {"id": "2", "label": "Perder esta oportunidade."}
]

def imprime_titulo(titulo):
    """Imprime um título formatado com uma linha acima e abaixo do texto."""
    print("\n" + "-" * 50)
    print(titulo.center(50))
    print("-" * 50)

def carregar_contatos():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela do tkinter
    arquivo_csv = filedialog.askopenfilename(title="Selecione o arquivo CSV dos contatos", filetypes=[("CSV Files", "*.csv")])
    return arquivo_csv

def carregar_textos():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela do tkinter
    arquivos_txt = filedialog.askopenfilenames(title="Selecione os arquivos de texto", filetypes=[("Text Files", "*.txt")])
    
    textos = []
    for arquivo in arquivos_txt:
        with open(arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
            textos.append(texto)
    
    return textos

def saudacao_por_horario():
    agora = datetime.now().hour
    if 6 <= agora < 12:
        return "Bom dia"
    elif 12 <= agora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def status_instancia():
    url = f"{BASE_URL}/status"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        return data['connected'], data.get('error', None), data['smartphoneConnected']
    else:
        print(f"Erro ao verificar status da instância. Status code: {response.status_code}")
        return None, None, None

def conectar(telefone):
    url = f"{BASE_URL}/phone-code/{telefone}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json().get('code')
    else:
        print(f"Erro ao pegar código para o telefone {telefone}. Status code: {response.status_code}")
        return None

def enviar_texto_simples(phone, message):
    url = f"{BASE_URL}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json()

def enviar_imagem(phone, message):
    url = f"{BASE_URL}/send-image"
    payload = {
        "phone": phone,
        "image": "https://i.ibb.co/G74xYR5/Tr-fego-Pago.png",
        "caption": message
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    return response.json()

def numero_tem_whatsapp(phone):
    url = f"{BASE_URL}/phone-exists/{phone}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def gerar_hash_lista(arquivo_csv):
    with open(arquivo_csv, 'rb') as file:
        return hashlib.md5(file.read()).hexdigest()

def salvar_status_envio(telefone):
    modo = 'a'
    with open(arquivo_status, modo) as file:
        writer = csv.writer(file)
        writer.writerow([telefone])

def telefone_ja_enviado(telefone):
    if not os.path.exists(arquivo_status):
        return False
    with open(arquivo_status, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Verifica se a linha não está vazia e se o telefone corresponde ao da linha
            if row and row[0] == telefone:
                return True
    return False

def log_message(message):
    global CAMINHO_ARQUIVO_LOG
    now = datetime.now().strftime("%H:%M:%S")
    with open(CAMINHO_ARQUIVO_LOG, 'a') as arquivo_log:
        arquivo_log.write(f"{now} | {message}\n")

def enviar_mensagem_em_massa(arquivo_csv=None, textos=None, tipo_mensagem='imagem', intervalo=(10, 20), max_envios=None):
    if not arquivo_csv:
        arquivo_csv = carregar_contatos() 
    if not textos:
        textos = carregar_textos()
    textos_ciclo = cycle(textos)
    count = 0
    with open(arquivo_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if max_envios and count >= max_envios:
                break
            row = {k.lower(): v for k, v in row.items()}
            phone = row.get('telefone', None)
            if telefone_ja_enviado(phone):
                print(f"O número {phone} já recebeu a mensagem anteriormente. Pulando...")
                log_message(f"O número {phone} já recebeu a mensagem anteriormente. Pulando...")
                continue
            whatsapp_status = numero_tem_whatsapp(phone)
            print(whatsapp_status)
            if whatsapp_status['exists'] == False:
                print(f"O número {phone} não possui WhatsApp. Pulando...")
                log_message(f"O número {phone} não possui WhatsApp. Pulando...")
                continue
            texto_atual = next(textos_ciclo)
            mensagem_formatada = texto_atual.format(saudacao=saudacao_por_horario(), **row)
            if tipo_mensagem == 'texto':
                enviar_texto_simples(phone, mensagem_formatada)
                print(f"O número {phone} recebeu a mensagem com sucesso!")
                log_message(f"O número {phone} recebeu a mensagem com sucesso!")
            elif tipo_mensagem == 'imagem':
                enviar_imagem(phone, mensagem_formatada)
                print(f"O número {phone} recebeu a mensagem com sucesso!")
                log_message(f"O número {phone} recebeu a mensagem com sucesso!")
            count += 1
            salvar_status_envio(phone)
            time.sleep(random.uniform(*intervalo))
    return count

def criar_nome_arquivo_log():
    agora = datetime.now()
    nome_arquivo = agora.strftime("%d%m%Y%H%M%S") + ".txt"
    return nome_arquivo

def main():
    global CAMINHO_ARQUIVO_LOG

    connected, error, smartphoneConnected = status_instancia()

    if connected:
        print("A instância já está conectada ao Z-API.")
        if not smartphoneConnected:
            print("No entanto, o smartphone não está conectado à internet.")
        nome_arquivo_log = criar_nome_arquivo_log()
        CAMINHO_ARQUIVO_LOG = os.path.join(pasta_raiz, nome_arquivo_log)
        with open(CAMINHO_ARQUIVO_LOG, 'w') as arquivo_log:
            arquivo_log.write("Log de envio de mensagens iniciado em: {}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        enviar_mensagem_em_massa(max_envios=200)
        
    else:
        if error:
            print(f"Erro: {error}")
            if error == "You are not connected.":
                telefone = input("Digite o número de telefone para conectar: ")
                codigo = conectar(telefone)
                
                if codigo:
                    print(f"Insira o seguinte código no WhatsApp: {codigo}")
                else:
                    print("Não foi possível obter o código para este número de telefone.")

if __name__ == "__main__":
    main()