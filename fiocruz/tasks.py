from __future__ import absolute_import, unicode_literals
import json
import pandas as pd
import os
from tqdm import tqdm
from celery import shared_task
from django.conf import settings
from fiocruz.models import Arquivos_virtaulS, Macromoleculas_virtaulS, Macro_Prepare
from django.core.mail import send_mail

from django.template.loader import render_to_string
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

from .utils.macro_prepare_comRedocking import (
    preparacao_gpf as preparacao_gpf_CR,
    run_autogrid as run_autogrid_CR,
    modifcar_fld as modifcar_fld_CR,
    run_autodock as run_autodock_CR,
)

from .utils.macro_prepare_semRedocking import (
    preparacao_gpf as preparacao_gpf_SR,
    run_autogrid as run_autogrid_SR,
    modifcar_fld as modifcar_fld_SR,
)

@shared_task
def add(x, y):
    return x + y



#Processo principal plamodocking com redocking
@shared_task
def plasmodocking_SR(username, id_processo, email_user):

    arquivos_vs = Arquivos_virtaulS.objects.get(id=id_processo) 
    
    #---------------------------------------------------------------------
    # criar pastas do usuario 
    dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome)
    diretorio_macromoleculas,diretorio_dlgs,diretorio_gbests,diretorio_lig_split,diretorio_ligantes_pdbqt = criar_diretorios(username, arquivos_vs.nome)

    #---------------------------------------------------------------------
    #preparação ligante
    preparar_ligantes(arquivos_vs,diretorio_lig_split,diretorio_ligantes_pdbqt)

    ligantes_pdbqt = listar_arquivos(diretorio_ligantes_pdbqt)
    
    #---------------------------------------------------------------------
    #execução do AutodockGPU
    macromoleculas = Macromoleculas_virtaulS.objects.all()
    
    data, tabela_final = [], []

    with tqdm(total=len(macromoleculas), desc=f'Plasmodocking usuario {username} processo {arquivos_vs.nome}') as pbar:
        for macromolecula in macromoleculas:
            receptor_data, data_data = preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs,diretorio_ligantes_pdbqt,diretorio_macromoleculas,username,arquivos_vs.nome)

            data.append(receptor_data)
            tabela_final.extend(data_data)

            # Atualize a barra de progresso
            pbar.update(1)
    #fim dos 2 for ligante e receptor
            
    remover_arquivos_xml(diretorio_dlgs, "*.xml")

    json_data = json.dumps(data, indent=4)  # Serializa os dados em JSON formatado
    
    # Especifique o caminho e nome do arquivo onde você deseja salvar o JSON
    file_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome,"dados.json")
    
    with open(file_path, 'w') as json_file:
        json_file.write(json_data)

    arquivos_vs.status = True
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

    enviar_email.delay(username,arquivos_vs.nome,email_user)

    
    return "task concluida com sucesso"


#Processo de envio de email
@shared_task
def enviar_email(usename,processo,email_user):
    context = {
        'subject': 'Processo Plasmodocking concluido.',
        'message': f'ola {usename}, O seu processo plasmodocking {processo} foi concluido com sucesso, resultado já disponivel na pagina de resutados.',
        
    }

    message = render_to_string('template.html', context)
    send_mail(
        'Plasmodocking Fiocruz/UNIR',
        'Corpo do E-mail',
        'plasmodockingteste@outlook.com',
        ['eduardohernany.pdm@gmail.com', email_user],
        html_message=message,  # Use a mensagem HTML renderizada
        )


    return "Email enviado com sucesso."


#Processo de preparação de macromolecula com redocking
@shared_task
def prepare_macro_SemRedocking(id_processo):

    macroPrepare = Macro_Prepare.objects.get(id=id_processo) 

    preparacao_gpf_SR(macroPrepare)

    run_autogrid_SR(macroPrepare)
    
    fld_text, fld_name = modifcar_fld_SR(macroPrepare)

    return fld_text, fld_name


@shared_task
def prepare_macro_ComRedocking(id_processo):

    macroPrepare = Macro_Prepare.objects.get(id=id_processo) 

    preparacao_gpf_CR(macroPrepare)

    run_autogrid_CR(macroPrepare)
    
    fld_text, fld_name = modifcar_fld_CR(macroPrepare)
    
    run_autodock_CR(macroPrepare)

    return fld_text, fld_name
