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

#Processo principal plamodocking sem redocking
@shared_task
def plasmodocking_SR(username, id_processo, email_user):
    arquivos_vs = ProcessPlasmodocking.objects.get(id=id_processo) 
    arquivos_vs.status = "processando"
    arquivos_vs.save()

    #---------------------------------------------------------------------
    # criar pastas do usuario 
    dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", arquivos_vs.nome)
    diretorio_macromoleculas,diretorio_dlgs,diretorio_gbests,diretorio_lig_split,diretorio_ligantes_pdbqt = criar_diretorios_SR(username, arquivos_vs.nome)
    #---------------------------------------------------------------------
    #preparação ligante
    preparar_ligantes_SR(arquivos_vs,diretorio_lig_split,diretorio_ligantes_pdbqt)

    ligantes_pdbqt = listar_arquivos(diretorio_ligantes_pdbqt)
    
    #---------------------------------------------------------------------
    #execução do AutodockGPU
    if arquivos_vs.type == 'falciparum' :
        macromoleculas = MacromoleculesFalciparumWithRedocking.objects.all()

        print("Macromoleculas Falciparum sem redocking")
    else:    
        macromoleculas = MacromoleculesFalciparumWithRedocking.objects.all()

        print("Macromoleculas Vivax sem redocking")
    
    data, tabela_final = [], []

    with tqdm(total=len(macromoleculas), desc=f'Plasmodocking usuario {username} processo {arquivos_vs.nome}') as pbar:
        for macromolecula in macromoleculas:
            receptor_data, data_data = preparar_dados_receptor_SR(macromolecula, ligantes_pdbqt, diretorio_dlgs,diretorio_ligantes_pdbqt,diretorio_macromoleculas,username,arquivos_vs.nome)

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

    #enviar_email.delay(username,arquivos_vs.nome,email_user)
    
    return "task concluida com sucesso"

#Processo principal plamodocking com redocking
@shared_task
def plasmodocking_CR(username, id_processo, email_user):
    try:
        # Recuperar o processo no banco de dados
        arquivos_vs = ProcessPlasmodocking.objects.get(id=id_processo) 
        arquivos_vs.status = "processando"
        arquivos_vs.save()

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
        
        with tqdm(total=len(macromoleculas), desc=f'Plasmodocking usuario {username} processo {arquivos_vs.nome}') as pbar:
            for macromolecula in macromoleculas:
                print("Macromolecula: "+macromolecula.rec)
                receptor_data, data_data = preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs, diretorio_ligantes_pdbqt,
                diretorio_macromoleculas,username,arquivos_vs.nome,arquivos_vs.type, arquivos_vs.redocking)
                data.append(receptor_data)
                tabela_final.extend(data_data)
                # Atualize a barra de progresso
                pbar.update(1)
                
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
        return "task concluida com sucesso"
    
    except Exception as e:
        # Em caso de erro, atualizar o status para "error"
        arquivos_vs.status = "error"
        arquivos_vs.save()
        print(f"Ocorreu um erro no processo: {str(e)}")
        return f"task falhou: {str(e)}"

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

    macroPrepare = MacroPrepare.objects.get(id=id_processo) 

    print("ok 1")

    preparacao_gpf_SR(macroPrepare)

    print("ok 2")

    #run_autogrid_SR(macroPrepare)
    
    #fld_text, fld_name = modifcar_fld_SR(macroPrepare)

    return "fld_text, fld_name"

@shared_task
def prepare_macro_ComRedocking(id_processo):
    macroPrepare = MacroPrepare.objects.get(id=id_processo) 

    pythonsh_path = os.path.expanduser("/home/autodockgpu/mgltools_x86_64Linux2_1.5.7/bin/pythonsh")
    prep_gpf_path = os.path.expanduser("/home/autodockgpu/mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_gpf4.py")
    autogrid_path = os.path.expanduser("/home/autodockgpu/x86_64Linux2/autogrid4")
    ad4_parameters_path = os.path.expanduser("/home/autodockgpu/x86_64Linux2/AD4_parameters.dat")

    centergrid = 'gridcenter={0}'.format(macroPrepare.gridcenter)
    sizegrid = 'npts={0}'.format(macroPrepare.gridsize)
    dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}")
    print(sizegrid)
    print(centergrid)
    receptor = os.path.join(settings.MEDIA_ROOT, str(macroPrepare.recptorpdbqt))
    
    lt1 = "ligand_types=C,A,N,NA,NS,OA,OS,SA,S,H,HD"
    lt2 = "ligand_types=HS,P,Br,BR,Ca,CA,Cl,CL,F,Fe,FE"
    lt3 = "ligand_types=I,Mg,MG,Mn,MN,Zn,ZN,He,Li,Be"
    lt4 = "ligand_types=B,Ne,Na,Al,Si,K,Sc,Ti,V,Co"
    lt5 = "ligand_types=Ni,Cu,Ga,Ge,As,Se,Kr,Rb,Sr,Y"
    lt6 = "ligand_types=Zr,Nb,Cr,Tc,Ru,Rh,Pd,Ag,Cd,In"
    lt7 = "ligand_types=Sn,Sb,Te,Xe,Cs,Ba,La,Ce,Pr,Nd"
    lt8 = "ligand_types=Pm,Sm,Eu,Gd,Tb,Dy,Ho,Er,Tm,Yb"
    lt9 = "ligand_types=Lu,Hf,Ta,W,Re,Os,Ir,Pt,Au,Hg"
    lt10 = "ligand_types=Tl,Pb,Bi,Po,At,Rn,Fr,Ra,Ac,Th"
    lt11 = "ligand_types=Pa,U,Np,Pu,Am,Cm,Bk,Cf,E,Fm"
    
    for i in range(1, 12):
        lt = f'{lt1 if i == 1 else lt2 if i == 2 else lt3 if i == 3 else lt4 if i == 4 else lt5 if i == 5 else lt6 if i == 6 else lt7 if i == 7 else lt8 if i == 8 else lt9 if i == 9 else lt10 if i == 10 else lt11  }'
        saida = os.path.join(dir_path, f'gridbox{i}.gpf')

        comando = [
            pythonsh_path, prep_gpf_path, "-r", receptor, "-o", saida, "-p", centergrid, "-p", sizegrid, "-p", lt
        ]
     # Executando o comando
        print(comando)

        process = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dir_path)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Erro: {stderr.decode()}")
        else:
            print(f"Sucesso: {stdout.decode()}")
        
        # Escrevendo no arquivo de log
        file_path = os.path.join(dir_path, 'teste.txt')
        with open(file_path, "a") as arquivo:
            arquivo.write(" ".join(comando) + "\n")
    
    print("ok 1")

    for i in range(1, 12):
        dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}")
        gpf_dir = os.path.join(dir_path, f'gridbox{i}.gpf')

        sed_command = f"sed -i '1i\\parameter_file {os.path.abspath(ad4_parameters_path)}' {gpf_dir}"
        print(sed_command)
        subprocess.run(sed_command, shell=True, check=True)

        autogrid_command = f"{autogrid_path} -p gridbox{i}.gpf -l gridbox.glg"
        print(autogrid_command)
        subprocess.run(autogrid_command, shell=True, check=True, cwd=dir_path)

    print("ok 2")

    dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}")

    filename_receptor, file_extension2 = macroPrepare.recptorpdb.name.split(".")

    parts = filename_receptor.split("/")
    
    file_path = f'{settings.MEDIA_ROOT}/{filename_receptor}.maps.fld'  # Substitua pelo caminho do seu arquivo
    line_number = 23

    # Ler o conteúdo do arquivo
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Verificar se o arquivo tem pelo menos 23 linhas
    if len(lines) >= line_number:
        # Manter as primeiras 23 linhas e descartar o restante
        new_lines = lines[:line_number]

        # Escrever as linhas de volta para o arquivo
        with open(file_path, 'w') as file:
            file.writelines(new_lines)

        print(f"Linhas abaixo da linha {line_number} foram removidas.")
    else:
        print(f"O arquivo tem menos de {line_number} linhas, nada foi removido.")

    texto = textfld()
    
    # Substituindo todas as ocorrências de 'macro' por 'receptor'
    novo_texto = texto.replace("kakakakaka", parts[-1])

    # Imprimindo o texto resultante
    with open(file_path, "a") as arquivo:
        # Escrevendo o novo texto no arquivo
        arquivo.write(novo_texto)

    # Fechando o arquivo
    arquivo.close()

    print("ok 3")

    return "fld_text, fld_name"
