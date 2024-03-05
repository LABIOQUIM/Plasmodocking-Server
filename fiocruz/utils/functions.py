import glob
import os
import shutil
import subprocess
from ..models import Arquivos_virtaulS, Macromoleculas_virtaulS, UserCustom, Macro_Prepare
from rest_framework import routers, serializers, viewsets
from django.http import FileResponse, HttpResponse, JsonResponse 
from django.contrib.auth.models import User
import json
from ..serializers import VS_Serializer
import pandas as pd

from django.conf import settings



def extrair_energia_ligacao(caminho_arquivo):
    # Variável para armazenar a energia de ligação
    binding_energy = None

    # Abra o arquivo em modo leitura
    with open(caminho_arquivo, 'r') as arquivo:
        # Percorra as linhas do arquivo
        for linha in arquivo:
            # Verifique se a linha contém a energia de ligação
            if 'RANKING' in linha:
                # Separe a linha por espaços em branco
                dados = linha.split()

                # Extraia a energia de ligação
                binding_energy = dados[3]
                run_energy = dados[2]
                break

    # Verifique se a energia de ligação foi encontrada
    if binding_energy is not None:
        return binding_energy,run_energy
    else:
        return "None"

#função para extrair o menor rmsd e sua energia da preparação da macromolecula
def extrair_menor_rmsd(caminho_arquivo):
    menor_rmsd = float('inf')  # Inicialize com um valor infinito positivo
    energia_rmsd = None  # Inicialize como None

    with open(caminho_arquivo, 'r') as arquivo:
        for linha in arquivo:
            if 'RANKING' in linha:
                dados = linha.split()
                if len(dados) >= 6:
                    binding_energy = float(dados[5])
                    if binding_energy < menor_rmsd:
                        menor_rmsd = binding_energy
                        energia_rmsd = dados[3]

    if energia_rmsd is not None:
        return menor_rmsd, energia_rmsd
    else:
        return None


def converter_sdf_para_pdb(diretorio_sdf):
    obabel_path= os.path.expanduser("/usr/bin/obabel")

    arquivos_sdf = glob.glob(os.path.join(diretorio_sdf, "*.sdf"))
    if not arquivos_sdf:
        return False

    comando = [obabel_path, "-isdf"] + arquivos_sdf + ["-opdb", "-O*.pdb"]
    executar_comando(comando, diretorio_sdf)
    return True

def executar_comando(command, dir_path):

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dir_path)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return HttpResponse(f"Ocorreu um erro: {stderr.decode()}")

    return True 


def remover_arquivos_xml(dir_path, type_arquivo):
    arquivos_xml = glob.glob(os.path.join(dir_path, type_arquivo))
    for arquivo_xml in arquivos_xml:
        try:
            os.remove(arquivo_xml)
        except Exception as e:
            print(f"Erro ao remover o arquivo {arquivo_xml}: {e}")


def listar_arquivos(diretorio):
    command = ["ls"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=diretorio)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return False, f"Ocorreu um erro: {stderr.decode()}"
    
    # Obtém a saída do comando como uma string
    saida = stdout.decode()
    # Remove espaços em branco adicionais e quebras de linha
    saida = saida.strip()
    # Divide a string em uma lista de strings
    ligantes_pdb = saida.split()

    return ligantes_pdb
