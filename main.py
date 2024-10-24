import os
import time
import mysql.connector
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re


# Função para verificar se já existe um registro e incrementar o total de imagens
def atualizar_total_imagens(equipamento, data, hora):
    try:
        # Conectar ao banco de dados MySQL
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="sitran123",
            database="sscb"
        )
        cursor = conexao.cursor()

        # Verificar se já existe um registro para o equipamento, data e hora
        consulta = """
            SELECT total_imagens FROM imagens 
            WHERE equipamento = %s AND data = %s AND hora = %s
        """
        valores_consulta = (equipamento, data, hora)
        cursor.execute(consulta, valores_consulta)
        resultado = cursor.fetchone()

        if resultado:
            # Se o registro existir, incrementa o total de imagens
            total_imagens_atual = resultado[0] + 1
            atualizar_sql = """
                UPDATE imagens 
                SET total_imagens = %s 
                WHERE equipamento = %s AND data = %s AND hora = %s
            """
            cursor.execute(atualizar_sql, (total_imagens_atual, equipamento, data, hora))
            print(f"Total de imagens atualizado para {total_imagens_atual} em {equipamento} {data} {hora}h")
        else:
            # Se não existir, insere um novo registro com total_imagens = 1
            inserir_sql = """
                INSERT INTO imagens (equipamento, data, hora, total_imagens) 
                VALUES (%s, %s, %s, %s)
            """
            valores_inserir = (equipamento, data, hora, 1)
            cursor.execute(inserir_sql, valores_inserir)
            print(f"Novo registro inserido para {equipamento}, {data} {hora}h, total_imagens = 1")

        conexao.commit()

    except mysql.connector.Error as err:
        print(f"Erro: {err}")
    finally:
        if conexao.is_connected():
            cursor.close()
            conexao.close()


# Classe que define o manipulador de eventos de criação de arquivos
class MonitoramentoArquivoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".jpg"):
            arquivo = os.path.basename(event.src_path)
            print(f"Novo arquivo detectado: {arquivo}")

            # Expressão regular para capturar as informações do nome do arquivo
            padrao = r"(\d{8})(\d{6})00200(\d{5})(\d{3})(\w{7})([DT])(\d{2})\d{6}(\d{6})"

            match = re.match(padrao, arquivo)

            if match:
                equipamento = match.group(3)
                data = match.group(1)
                hora = match.group(2)

                # Atualizar o total de imagens no banco de dados
                atualizar_total_imagens(equipamento, data, hora)
            else:
                print(f"Nome de arquivo {arquivo} não corresponde ao padrão esperado.")


# Função principal para iniciar o monitoramento
def monitorar_diretorio(caminho_diretorio):
    evento_handler = MonitoramentoArquivoHandler()
    observador = Observer()
    observador.schedule(evento_handler, caminho_diretorio, recursive=True)
    observador.start()

    print(f"Iniciando monitoramento do diretório: {caminho_diretorio}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observador.stop()
    observador.join()


# Caminho do diretório a ser monitorado
diretorio_para_monitorar = "//10.0.170.14/dados/"
monitorar_diretorio(diretorio_para_monitorar)