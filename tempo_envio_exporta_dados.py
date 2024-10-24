import os
from datetime import datetime
import time
import pytz
import sqlite3

def listar_equipamentos(diretorio_lista_equipamentos):
    with open(diretorio_lista_equipamentos, 'r') as file:
        lista = [linha.strip() for linha in file]
    return lista

def hora_atual_fuso_horario(fuso_horario, data_hora_utc):
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    fuso_amazonas = pytz.timezone('America/Cuiaba')
    fuso_acre = pytz.timezone('America/Rio_Branco')

    if fuso_horario == '0':
        agora = data_hora_utc.astimezone(fuso_brasilia)
    elif fuso_horario == '1':
        agora = data_hora_utc.astimezone(fuso_amazonas)
    elif fuso_horario == '2':
        agora = data_hora_utc.astimezone(fuso_acre)

    return agora

def aplicar_fuso_horario(fuso_horario, data_hora):
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    fuso_amazonas = pytz.timezone('America/Cuiaba')
    fuso_acre = pytz.timezone('America/Rio_Branco')

    if fuso_horario == '0':
        data_hora_fuso_horario = fuso_brasilia.localize(data_hora)
    elif fuso_horario == '1':
        data_hora_fuso_horario = fuso_amazonas.localize(data_hora)
    elif fuso_horario == '2':
        data_hora_fuso_horario = fuso_acre.localize(data_hora)

    return data_hora_fuso_horario

def obter_data_hora_captura(nome_arquivo):
    data_hora_str = nome_arquivo[:14]
    return datetime.strptime(data_hora_str, "%Y%m%d%H%M%S")

def calcular_tempo_envio(fuso_horario, data_hora_captura, caminho_arquivo):
    data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
    data_criacao_fuso = pytz.timezone('America/Sao_Paulo').localize(data_criacao)
    data_criacao_utc = data_criacao_fuso.astimezone(pytz.utc)

    data_hora_captura_fuso = aplicar_fuso_horario(fuso_horario, data_hora_captura)
    data_hora_captura_utc = data_hora_captura_fuso.astimezone(pytz.utc)

    tempo_envio = data_criacao_utc - data_hora_captura_utc
    return tempo_envio

def calcular_tempo_desde_ultima_captura(fuso_horario, data_hora_captura):
    data_hora_captura_fuso = aplicar_fuso_horario(fuso_horario, data_hora_captura)
    data_hora_captura_utc = data_hora_captura_fuso.astimezone(pytz.utc)

    utc = pytz.utc
    agora_utc = datetime.now(utc)

    tempo_ultima_captura = agora_utc - data_hora_captura_utc
    return tempo_ultima_captura

def verificar_arquivos(diretorio_equipamento):
    arquivo_mais_recente = None
    data_hora_mais_recente = None

    for subdir, _, arquivos in os.walk(diretorio_equipamento):
        for arquivo in arquivos:
            if arquivo.endswith('.jpg'):
                try:
                    data_hora_captura = obter_data_hora_captura(arquivo)

                    if data_hora_mais_recente is None or data_hora_captura > data_hora_mais_recente:
                        data_hora_mais_recente = data_hora_captura
                        arquivo_mais_recente = os.path.join(subdir, arquivo)

                except ValueError:
                    continue

    return arquivo_mais_recente, data_hora_mais_recente

def inicializar_banco(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TempoEnvio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Codigo_Equipamento TEXT NOT NULL,
            Tempo_Envio TEXT,
            Tempo_desde_ultima_captura TEXT,
            data_hora_mais_recente TEXT
        )
    ''')
    conn.commit()
    conn.close()

def inserir_dados(db_name, codigo_equipamento, tempo_envio, tempo_desde_ultima_captura, data_hora_mais_recente):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO TempoEnvio (Codigo_Equipamento, Tempo_Envio, Tempo_desde_ultima_captura, data_hora_mais_recente)
        VALUES (?, ?, ?, ?)
    ''', (codigo_equipamento, str(tempo_envio), str(tempo_desde_ultima_captura), data_hora_mais_recente))
    conn.commit()
    conn.close()

def processar_equipamentos(diretorio_base, lista_equipamentos, db_name):
    inicializar_banco(db_name)

    utc = pytz.utc
    data_hora_utc = datetime.now(utc)

    for item in lista_equipamentos:
        codigo_equipamento = item.split(';')[0]
        fuso_horario = item.split(';')[1]

        agora = hora_atual_fuso_horario(fuso_horario, data_hora_utc)

        ano_atual = agora.strftime("%Y")
        mes_atual = agora.strftime("%m").zfill(2)
        dia_atual = agora.strftime("%d").zfill(2)
        hora_atual = agora.strftime("%H")
        mes_dia_atual = mes_atual + dia_atual

        diretorio_equipamento = os.path.join(diretorio_base, codigo_equipamento, ano_atual, mes_dia_atual, str(hora_atual).zfill(4))

        if os.path.exists(diretorio_equipamento):
            arquivo_mais_recente, data_hora_mais_recente = verificar_arquivos(diretorio_equipamento)

            if arquivo_mais_recente and data_hora_mais_recente:
                tempo_envio = calcular_tempo_envio(fuso_horario, data_hora_mais_recente, arquivo_mais_recente)
                tempo_desde_ultima_captura = calcular_tempo_desde_ultima_captura(fuso_horario, data_hora_mais_recente)

                # Inserir dados no banco de dados
                inserir_dados(db_name, codigo_equipamento, tempo_envio, tempo_desde_ultima_captura, data_hora_mais_recente.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                # Inserir dados mesmo que não haja arquivos
                inserir_dados(db_name, codigo_equipamento, "N/A", "N/A", "N/A")
        else:
            # Inserir dados se o diretório não existe
            inserir_dados(db_name, codigo_equipamento, "N/A", "N/A", "N/A")

# Exemplo de uso:
if __name__ == "__main__":
    while True:
        diretorio_base = "//10.0.170.14/DADOS/"
        diretorio_dados = 'dados/'
        diretorio_lista_equipamentos = os.path.join(diretorio_dados, 'lista_equipamentos_completa_fuso.txt')
        db_name = 'dados_tempo_envio.db'
        lista_equipamentos = listar_equipamentos(diretorio_lista_equipamentos)
        processar_equipamentos(diretorio_base, lista_equipamentos, db_name)

        time.sleep(10)
