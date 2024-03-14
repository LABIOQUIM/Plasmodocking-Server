import os
import subprocess
from django.http import  HttpResponse
from django.conf import settings

from ..util import (
    textfld,
)


def preparacao_gpf(macroPrepare):
    pythonsh_path = os.path.expanduser("~/mgltools_x86_64Linux2_1.5.7/bin/pythonsh")
    prep_gpf_path= os.path.expanduser("~/mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_gpf4.py")
    prep_recptor_path= os.path.expanduser("~/mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py")
#-------------preparação gpf------------------------
    centergrid = 'gridcenter={0}'.format(macroPrepare.gridcenter)
    sizegrid = 'npts={0}'.format(macroPrepare.gridsize)

    dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}")

    

    receptor = os.path.join(settings.MEDIA_ROOT, str(macroPrepare.recptorpdb))
    #preparar o receptor
    comando = [pythonsh_path, prep_recptor_path, "-r", receptor]
    receptorpdbqt = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}", f"{macroPrepare.rec}_a.pdbqt")

    success, error_msg = processar_comando(comando, dir_path)
    if not success:
        return HttpResponse(f"Ocorreu um erro: {error_msg}")

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

    comandos = []

    for i in range(1, 12):
        lt = f'{lt1 if i == 1 else lt2 if i == 2 else lt3 if i == 3 else lt4 if i == 4 else lt5 if i == 5 else lt6 if i == 6 else lt7 if i == 7 else lt8 if i == 8 else lt9 if i == 9 else lt10 if i == 10 else lt11  }'
        saida = os.path.join(dir_path, f'gridbox{i}.gpf')

        comando = [
            pythonsh_path, prep_gpf_path, "-r", receptorpdbqt, "-o", saida, "-p", centergrid, "-p", sizegrid, "-p", lt
        ]
        comandos.append(comando)

    for comando in comandos:
        success, error_msg = processar_comando(comando, dir_path)
        if not success:
            return HttpResponse(f"Ocorreu um erro: {error_msg}")
    
    



def run_autogrid(macroPrepare):
    dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", macroPrepare.processo_name, f"{macroPrepare.rec}")
    autogrid_path=  os.path.expanduser("~/x86_64Linux2/autogrid4")
    ad4_parameters_path = os.path.expanduser("~/x86_64Linux2/AD4_parameters.dat")

    #for filename in glob.glob("*.gpf"):
    for i in range(1, 12):
        gpf_dir = os.path.join(dir_path, f'gridbox{i}.gpf')

        sed_command = f"sed -i '1i\\parameter_file {os.path.abspath(ad4_parameters_path)}' {gpf_dir}"
        subprocess.run(sed_command, shell=True, check=True)

        autogrid_command = f"{autogrid_path} -p gridbox{i}.gpf -l gridbox.glg"
        subprocess.run(autogrid_command, shell=True, check=True, cwd=dir_path)



def modifcar_fld(macroPrepare):
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
    novo_texto = texto.replace("macro", parts[-1])

    # Imprimindo o texto resultante
    with open(file_path, "a") as arquivo:
        # Escrevendo o novo texto no arquivo
        arquivo.write(novo_texto)

    # Fechando o arquivo
    arquivo.close()

    return novo_texto, f"{parts[-1]}.maps.fld"


def processar_comando(command, cwd):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return False, stderr.decode()
        return True, None
    except Exception as e:
        return False, str(e)