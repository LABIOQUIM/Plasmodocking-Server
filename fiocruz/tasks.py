from __future__ import absolute_import, unicode_literals
import glob
import json
from pathlib import Path
import shutil
import subprocess
import pandas as pd
import os
from tqdm import tqdm
from celery import shared_task
from django.conf import settings
from .models import ProcessPlasmodocking, MacromoleculesFalciparumWithRedocking, UserCustom, MacroPrepare, MacromoleculesFalciparumWithoutRedocking
from fiocruz.models import ProcessPlasmodocking, MacromoleculesFalciparumWithRedocking, MacroPrepare, MacromoleculesFalciparumWithoutRedocking, MacromoleculesVivaxWithRedocking
from django.core.mail import send_mail

from django.template.loader import render_to_string

import pusher

from fiocruz.util import textfld
from .utils.functions import (
    executar_comando,
    extrair_energia_ligacao,
    remover_arquivos_xml,
    listar_arquivos,
)

from .utils.plasmodocking_run import (
    criar_diretorios,
    preparar_ligantes,
    preparar_dados_receptor,
)

from .utils.plasmodocking_run_SR import (
    criar_diretorios as criar_diretorios_SR,
    preparar_ligantes as preparar_ligantes_SR,
    preparar_dados_receptor as preparar_dados_receptor_SR,
)

from .utils.macro_prepare_comRedocking import (
    preparacao_gpf as preparacao_gpf_CR,
    run_autogrid as run_autogrid_CR,
    modifcar_fld as modifcar_fld_CR,
    run_autodock as run_autodock_CR,
)

from .utils.macro_prepare_comRedocking import (
    preparacao_gpf as preparacao_gpf_SR,
    run_autogrid as run_autogrid_SR,
    modifcar_fld as modifcar_fld_SR,
)

@shared_task
def add(x, y):
    return x + y

#Processo principal plamodocking com redocking
@shared_task
def plasmodocking_CR(username, id_processo, email_user):
    try:
        pusher_client = pusher.Pusher(
            app_id='1893887',
            key='3494316859bbb0bb994e',
            secret='bc72a625817c1b30816b',
            cluster='sa1',
            ssl=True
        )
        
        # Recuperar o processo no banco de dados
        arquivos_vs = ProcessPlasmodocking.objects.get(id=id_processo) 
        arquivos_vs.status = "processando"
        arquivos_vs.save()
        
        pusher_client.trigger(username, 'proces', {
            "type": "chat_message",
            "proces": f"{arquivos_vs.id}",
            "status": f"init",
            "progress": f"0",
            "message": f"Iniciando proceso {arquivos_vs.nome}..."
        })
        
        # Criar pastas do usuário
        dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome)
        diretorio_macromoleculas, diretorio_dlgs, diretorio_gbests, diretorio_lig_split, diretorio_ligantes_pdbqt = criar_diretorios(username, arquivos_vs.nome)

        # Preparação dos ligantes
        preparar_ligantes(arquivos_vs, diretorio_lig_split, diretorio_ligantes_pdbqt)
        ligantes_pdbqt = listar_arquivos(diretorio_ligantes_pdbqt)

        # Separação por tipo e redocking
        print(f"type: {arquivos_vs.type} | redocking: {arquivos_vs.redocking}")
        
        if arquivos_vs.type == 'falciparum' and arquivos_vs.redocking:
            macromoleculas = MacromoleculesFalciparumWithRedocking.objects.all()
            print("Macromoleculas Falciparum com redocking")
            
        elif arquivos_vs.type == 'falciparum' and not arquivos_vs.redocking:
            macromoleculas = MacromoleculesFalciparumWithoutRedocking.objects.all()
            print("Macromoleculas Falciparum sem redocking")
            
        elif arquivos_vs.type == 'vivax' and arquivos_vs.redocking:
            macromoleculas = MacromoleculesVivaxWithRedocking.objects.all()
            print("Macromoleculas Vivax com redocking")
            
        # return f"task concluida com sucesso: {arquivos_vs.type} | {arquivos_vs.redocking}"
    
        data, tabela_final = [], []
        total_macromoleculas = len(macromoleculas)
        
        # =========================================================================================================================================
        autodockgpu_path = os.path.expanduser("/home/autodockgpu/AutoDock-GPU/bin/autodock_gpu_128wi")
        obabel_path = os.path.expanduser("/usr/bin/obabel")
        # =========================================================================================================================================
        
        
        with tqdm(total=len(macromoleculas), desc=f'Plasmodocking usuario {username} processo {arquivos_vs.nome}') as pbar:
            
            for index, macromolecula in enumerate(macromoleculas):
                
                porcentagem = ((index + 1) / total_macromoleculas) * 100
                
                print("Macromolecula: "+macromolecula.rec)
                receptor_data_oficial = None
                data_data_oficial = None
                # =========================================================================================================================================
                # macromolecula, ligantes_pdbqt, diretorio_dlgs, diretorio_ligantes_pdbqt, diretorio_macromoleculas, username, nome, type, redocking
                # receptor_data, data_data = preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs, diretorio_ligantes_pdbqt,
                # diretorio_macromoleculas,username,arquivos_vs.nome,arquivos_vs.type, arquivos_vs.redocking)
                
                
                # =========================================================================================================================================
                redocking = arquivos_vs.redocking
                type = arquivos_vs.type
                nome= arquivos_vs.nome
                receptor_data = {
                    'receptor_name': macromolecula.rec,
                    'molecule_name': macromolecula.nome,
                    'grid_center': macromolecula.gridcenter,
                    'grid_size': macromolecula.gridsize,
                    'ligante_original': macromolecula.ligante_original,
                    'energia_original': macromolecula.energia_original,
                    'rmsd_redocking': macromolecula.rmsd_redocking,
                    'ligantes': []
                } 

                print(" Nome molecula: " + macromolecula.nome)

                data_data = []
                
                # Define o diretório base para macromoléculas conforme o tipo e o redocking
                def obter_diretorio_macromoleculas(macromolecula, type, redocking):
                    if type == 'falciparum' and redocking:
                        return os.path.join(settings.MEDIA_ROOT, "macromoleculas", "falciparum", "comRedocking", macromolecula.rec)
                    elif type == 'falciparum' and not redocking:
                        return os.path.join(settings.MEDIA_ROOT, "macromoleculas", "falciparum", "semRedocking", macromolecula.rec)
                    elif type == 'vivax' and redocking:
                        return os.path.join(settings.MEDIA_ROOT, "macromoleculas", "vivax", "comRedocking", macromolecula.rec)
                    else:
                        raise ValueError("Tipo e condição de redocking não suportados.")
                
                dir_path = obter_diretorio_macromoleculas(macromolecula, type, redocking)
                print(f"Diretório macromoléculas: {dir_path}")
                
                for ligante_pdbqt in ligantes_pdbqt:
                    dir_ligante_pdbqt = os.path.join(diretorio_ligantes_pdbqt, ligante_pdbqt)
                    filename_ligante, _ = os.path.splitext(ligante_pdbqt)

                    r = str(macromolecula.rec_fld)
                    rec_maps_fld_path = os.path.join(settings.MEDIA_ROOT, r)
                    saida = os.path.join(diretorio_dlgs, f"{filename_ligante}_{macromolecula.rec}")
                    
                    # Executa docking com AutoDock-GPU
                    command = [
                        autodockgpu_path, 
                        "--ffile", rec_maps_fld_path, 
                        "--lfile", dir_ligante_pdbqt, 
                        "--gbest", "1", 
                        "--resnam", saida,
                        '--nrun', "100"
                    ]
                    
                    executar_comando(command, dir_path)
                    
                    arquivos_pdbqt = glob.glob(os.path.join(dir_path, "*.pdbqt"))

                    if arquivos_pdbqt:
                        print("Arquivos .pdbqt encontrados:")
                        for arquivo in arquivos_pdbqt:
                            print(arquivo)
                
                    # Configura caminho para o arquivo de melhor ligação (gbest)
                    diretorio_gbest_ligante_unico = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", nome, "gbest_pdb", filename_ligante)
                    os.makedirs(diretorio_gbest_ligante_unico, exist_ok=True)
                    
                    #==================================================
                    # Padrões de arquivos possíveis: "best.pdbqt" ou "<ligante>-best.pdbqt"
                    padroes_arquivos = [
                        os.path.join(dir_path, "best.pdbqt"),
                        os.path.join(dir_path, f"{Path(filename_ligante).stem}-best.pdbqt"),
                    ]

                    # Procurar pelos arquivos de saída possíveis
                    arquivo_encontrado = None
                    for padrao in padroes_arquivos:
                        if os.path.exists(padrao):
                            arquivo_encontrado = padrao
                            break

                    bsaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdbqt")

                    # Move o arquivo de melhor ligação, se encontrado
                    if arquivo_encontrado:
                        shutil.move(arquivo_encontrado, bsaida)
                        print(f"Arquivo {arquivo_encontrado} movido para {bsaida}.")
                    else:
                        print("Nenhum arquivo de melhor ligação foi encontrado ('best.pdbqt' ou '<ligante>-best.pdbqt').")
                    #==================================================
                    
                    # Converte o arquivo .pdbqt para .pdb com Open Babel
                    csaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdb")
                    command = [obabel_path, bsaida, "-O", csaida]
                    executar_comando(command, diretorio_gbest_ligante_unico)

                    # Remove o arquivo temporário .pdbqt
                    executar_comando(["rm", bsaida], dir_path)
                    
                    # Copia arquivos de macromoléculas específicos para o diretório de destino
                    sufixos = ['_A.pdb', '_a.pdb', '_ab.pdb', '_bd.pdb', '.pdb', '_macro', '_oficial', '_MACRO_COFATOR']
                    for sufixo in sufixos:
                        arquivo_path = os.path.join(dir_path, f"{macromolecula.rec}{sufixo}")
                        if os.path.exists(arquivo_path):
                            shutil.copy2(arquivo_path, diretorio_macromoleculas)
                            break
                    
                    # Extrai a melhor energia de ligação do arquivo .dlg
                    caminho_arquivo = f"{saida}.dlg"
                    best_energia, run = extrair_energia_ligacao(caminho_arquivo)
                    
                    ligante_data = {
                        'ligante_name': filename_ligante,
                        'ligante_energia': best_energia,
                        'run': run,
                    }
                    
                    receptor_data['ligantes'].append(ligante_data)
                    
                    # Adiciona dados para CSV
                    csv_data = {
                        'RECEPTOR_NAME': macromolecula.rec,
                        'LIGANTE_CID': filename_ligante,
                        'LIGANTE_MELHOR_ENERGIA': best_energia,
                        'RUN': run,
                    }
                    
                    if redocking:
                        csv_data.update({
                            'LIGANTE_REDOCKING': macromolecula.ligante_original,
                            'ENERGIA_REDOCKING': macromolecula.energia_original,
                        })
                    data_data.append(csv_data)

                receptor_data_oficial = receptor_data
                data_data_oficial = data_data                                              
                                                                   
                # =========================================================================================================================================
                data.append(receptor_data_oficial)
                tabela_final.extend(data_data_oficial)
                # Atualize a barra de progresso
                pbar.update(1)
                
                pusher_client.trigger(username, 'proces', {
                    "type": "chat_message",
                    "proces": f"{arquivos_vs.id}",
                    "status": f"running",
                    "progress": f"{porcentagem:.2f}",
                    "message": f"Processando macromolécula {macromolecula.rec} - {macromolecula.nome} "
                })
                
        #fim dos 2 for ligante e receptor    
        remover_arquivos_xml(diretorio_dlgs, "*.xml")
        json_data = json.dumps(data, indent=4) 
        
        # Especifique o caminho e nome do arquivo onde você deseja salvar o JSON
        file_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome,"dados.json")
        with open(file_path, 'w') as json_file:
            json_file.write(json_data)
        arquivos_vs.status = "concluido"
        arquivos_vs.resultado_final = json_data
        arquivos_vs.save()
        file_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome)
        dfdf = pd.DataFrame(tabela_final)
        csv_file_path = os.path.join(file_path, 'dadostab.csv')
        dfdf.to_csv(csv_file_path, sep=';', index=False)
        
        #----------------zip file---------------
        dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}")
        command = ["zip", "-r", arquivos_vs.nome+"/"+arquivos_vs.nome+".zip", arquivos_vs.nome]
        executar_comando(command, dir_path)
        ##enviar_email.delay(username,arquivos_vs.nome,email_user)
        
        pusher_client.trigger(username, 'proces', {
            "type": "chat_message",
            "proces": f"{arquivos_vs.id}",
            "status": f"done",
            "progress": f"100",
            "message": f"Processo {arquivos_vs.nome} concluído com sucesso"
        })

        return "task concluida com sucesso"
    
    except Exception as e:
        # Em caso de erro, atualizar o status para "error"
        arquivos_vs.status = "error"
        arquivos_vs.save()
        
        pusher_client.trigger(username, 'proces', {
            "type": "chat_message",
            "proces": f"{arquivos_vs.id}",
            "status": f"done",
            "progress": f"0",
            "message": f"Processo {arquivos_vs.nome} finalizado com erro!"
        })

        print(f"Ocorreu um erro no processo: {str(e)}")
        return f"task falhou: {str(e)}"

