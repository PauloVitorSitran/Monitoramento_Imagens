import os
from datetime import datetime
import time
import pytz

#EQUIPAMENTOS COM FUSO HORÁRIO COMO FAZER ?

def listar_equipamentos(diretorio_lista_equipamentos):
    with open(diretorio_lista_equipamentos, 'r') as file:
        lista = [linha.strip() for linha in file]

    return lista

def hora_atual_fuso_horario(fuso_horario, data_hora_utc):

    fuso_brasilia = pytz.timezone('America/Sao_Paulo')  # Fuso Horário de Brasília (UTC-3) ID 0
    fuso_amazonas = pytz.timezone('America/Cuiaba')  # Fuso Horário de Brasília (UTC-3) ID 1
    fuso_acre = pytz.timezone('America/Rio_Branco')  # Fuso Horário do Acre (UTC-5) ID 2

    # Obter a data e hora atuais conforme fuso horário
    if fuso_horario == '0':
        agora = data_hora_utc.astimezone(fuso_brasilia)
    elif fuso_horario == '1':
        agora = data_hora_utc.astimezone(fuso_amazonas)
    elif fuso_horario == '2':
        agora = data_hora_utc.astimezone(fuso_acre)

    return agora

def aplicar_fuso_horario(fuso_horario, data_hora):

    fuso_brasilia = pytz.timezone('America/Sao_Paulo')  # Fuso Horário de Brasília (UTC-3) ID 0
    fuso_amazonas = pytz.timezone('America/Cuiaba')  # Fuso Horário de Brasília (UTC-3) ID 1
    fuso_acre = pytz.timezone('America/Rio_Branco')  # Fuso Horário do Acre (UTC-5) ID 2

    # Obter a data e hora atuais conforme fuso horário
    if fuso_horario == '0':
        data_hora_fuso_horario = fuso_brasilia.localize(data_hora)
    elif fuso_horario == '1':
        data_hora_fuso_horario = fuso_amazonas.localize(data_hora)
    elif fuso_horario == '2':
        data_hora_fuso_horario = fuso_acre.localize(data_hora)

    return data_hora_fuso_horario

def obter_data_hora_captura(nome_arquivo):
    """Extrai os primeiros 14 caracteres do nome do arquivo e converte para datetime."""
    data_hora_str = nome_arquivo[:14]
    return datetime.strptime(data_hora_str, "%Y%m%d%H%M%S")

def calcular_tempo_envio(fuso_horario, data_hora_captura, caminho_arquivo):
    """Calcula a diferença entre a data de criação do arquivo e a data de captura."""
    data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_arquivo)) # Identifica a data de criação do arquivo
    data_criacao_fuso = pytz.timezone('America/Sao_Paulo').localize(data_criacao) # Aplica o fuso horário de Brasília
    data_criacao_utc = data_criacao_fuso.astimezone(pytz.utc) # Converte para o fuso UTC

    data_hora_captura_fuso = aplicar_fuso_horario(fuso_horario, data_hora_captura) # Aplica o fuso horário conforme localidade do equipamento
    data_hora_captura_utc = data_hora_captura_fuso.astimezone(pytz.utc) # Converte para o fuso UTC

    tempo_envio = data_criacao_utc - data_hora_captura_utc # Calcula o tmepo de envio usando as datas com fuso UTC
    return tempo_envio

def verificar_arquivos(diretorio_equipamento):
    """Verifica o diretório de um equipamento e encontra o arquivo mais recente com base na data de captura."""
    arquivo_mais_recente = None
    data_hora_mais_recente = None

    # Percorrer todas as subpastas e arquivos do equipamento
    for subdir, _, arquivos in os.walk(diretorio_equipamento):
        for arquivo in arquivos:
            if arquivo.endswith('.jpg'):
                try:
                    # Obter a data e hora de captura do nome do arquivo
                    data_hora_captura = obter_data_hora_captura(arquivo)

                    # Se não há arquivo mais recente, ou se esse é mais recente, atualizamos
                    if data_hora_mais_recente is None or data_hora_captura > data_hora_mais_recente:
                        data_hora_mais_recente = data_hora_captura
                        arquivo_mais_recente = os.path.join(subdir, arquivo)

                except ValueError:
                    # Caso o nome do arquivo não siga o formato esperado, podemos ignorar
                    continue

    return arquivo_mais_recente, data_hora_mais_recente

def registrar_tempo_envio(codigo_equipamento, status, tempo_envio=None, arquivo_mais_recente=None):
    """Registra o resultado no arquivo de log."""
    with open("log_tempo_envio.txt", "a", encoding="utf-8") as log:
        if status == "inexistente":
            log.write(f"Equipamento {codigo_equipamento}: Pasta inexistente.\n")
        else:
            log.write(f"Equipamento {codigo_equipamento}: Tempo de envio {tempo_envio}: Imagem {arquivo_mais_recente}.\n")

def processar_equipamentos(diretorio_base, lista_equipamentos):
    with open("log_tempo_envio.txt", "a", encoding="utf-8") as log:
        log.write(f"Início em {datetime.now()}\n")

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
            # Verificar o arquivo mais recente no diretório atual
            arquivo_mais_recente, data_hora_mais_recente = verificar_arquivos(diretorio_equipamento)

            if arquivo_mais_recente and data_hora_mais_recente:
                # Calcular o tempo de envio
                tempo_envio = calcular_tempo_envio(fuso_horario, data_hora_mais_recente, arquivo_mais_recente)
                # Registrar o tempo de envio
                registrar_tempo_envio(codigo_equipamento, "encontrado", tempo_envio, arquivo_mais_recente)
            else:
                # Se não há arquivos na pasta, registrar como inexistente
                registrar_tempo_envio(codigo_equipamento, "inexistente")
        else:
            # Pasta não encontrada, registrar como inexistente
            registrar_tempo_envio(codigo_equipamento, "inexistente")

# Exemplo de uso:
if __name__ == "__main__":

    while True:

        with open("log_tempo_envio.txt", "w", encoding="utf-8") as log:
            log.write("")  # Esta linha é opcional, mas você pode usar para deixar claro que o arquivo está vazio.

        diretorio_base = "//10.0.170.14/DADOS/"  # Defina o caminho base onde estão os diretórios dos equipamentos
        diretorio_dados = 'dados/'
        diretorio_lista_equipamentos = os.path.join(diretorio_dados, 'lista_equipamentos_completa_fuso.txt')
        lista_equipamentos = listar_equipamentos(diretorio_lista_equipamentos)
        processar_equipamentos(diretorio_base, lista_equipamentos)
        with open("log_tempo_envio.txt", "a", encoding="utf-8") as log:
            log.write(f"Fim em {datetime.now()}\n")

        time.sleep(10)