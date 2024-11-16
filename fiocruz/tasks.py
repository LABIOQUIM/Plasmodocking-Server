from __future__ import absolute_import, unicode_literals
import json
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
        
        with tqdm(total=len(macromoleculas), desc=f'Plasmodocking usuario {username} processo {arquivos_vs.nome}') as pbar:
            
            for index, macromolecula in enumerate(macromoleculas):
                
                porcentagem = ((index + 1) / total_macromoleculas) * 100
                
                print("Macromolecula: "+macromolecula.rec)
                receptor_data, data_data = preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs, diretorio_ligantes_pdbqt,
                diretorio_macromoleculas,username,arquivos_vs.nome,arquivos_vs.type, arquivos_vs.redocking)
                data.append(receptor_data)
                tabela_final.extend(data_data)
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

