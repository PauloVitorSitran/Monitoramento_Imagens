import os
import time
from datetime import datetime


def verificar_arquivos_recente_equipamentos(path_base, codigo_equipamento):
    numero_arquivos = 0

    # Montar o caminho da pasta correspondente ao código do equipamento e data/hora
    ano = '2024'
    mes_dia = '1023'
    hora = '15'

    # Exemplo de estrutura: Codigo_Equipamento > Ano > Mes_Dia > Hora
    caminho_pasta = os.path.join(path_base, codigo_equipamento, ano, mes_dia, hora.zfill(4))

    # Verificar se a pasta existe
    if os.path.exists(caminho_pasta):
        #print(f"Verificando arquivos na pasta: {caminho_pasta}")

        # Listar e verificar arquivos .jpg dentro da pasta
        for file in os.listdir(caminho_pasta):
            if file.endswith(".jpg"):
                numero_arquivos +=1
                file_path = os.path.join(caminho_pasta, file)
                file_size = os.path.getsize(file_path)
                creation_time = time.ctime(os.path.getctime(file_path))

    return numero_arquivos

def obter_lista_equipamentos(path_base):

    codigos_equipamentos = []

    # Listar diretórios no diretório raiz
    for nome_pasta in os.listdir(path_base):
        if len(nome_pasta) == 10 and nome_pasta[:5] == '00200':
            caminho_completo = os.path.join(path_base, nome_pasta)
            # Verificar se é uma pasta (presume-se que os códigos de equipamentos são pastas)
            if os.path.isdir(caminho_completo):
                codigos_equipamentos.append(nome_pasta)

    return codigos_equipamentos


if __name__ == "__main__":
    # Caminho base onde as pastas de equipamentos estão localizadas
    path_base = "//10.0.170.14/DADOS/"

    print(f'Monitorando pasta {path_base}')
    inicio = datetime.now()
    print(f'Início em {inicio}')

    try:
        while True:
            # Obter lista de equipamentos dinamicamente
            codigos_equipamentos = obter_lista_equipamentos(path_base)


            total_arquivos = 0

            # Verificar os arquivos recentes para cada equipamento
            for codigo in codigos_equipamentos:
                numero_arquivos = verificar_arquivos_recente_equipamentos(path_base, codigo)
                total_arquivos = total_arquivos + numero_arquivos
                print(f'Equipamento {codigo} Arquivos: {str(numero_arquivos).zfill(6)} Total {str(total_arquivos).zfill(6)}')

            # Definir o intervalo de tempo entre verificações (ex: 5 minutos)
            time.sleep(10)


    except KeyboardInterrupt:
        print("Monitoramento interrompido pelo usuário.")