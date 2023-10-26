import os
import shutil

from django.conf import settings

from .functions import (
    extrair_energia_ligacao,
    converter_sdf_para_pdb,
    executar_comando,
    remover_arquivos_xml,
    listar_arquivos,
)


def criar_diretorios(username, nome):
    # Diretório raiz
    dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", nome)
    
    # Diretório para as macromoléculas/receptores utilizados
    diretorio_macromoleculas = os.path.join(dir_path, "macromoleculas")
    os.makedirs(diretorio_macromoleculas)
    
    # Diretório para os arquivos .dlgs gerados no processo
    diretorio_dlgs = os.path.join(dir_path, "arquivos_dlgs")
    os.makedirs(diretorio_dlgs)
    
    # Diretório para os arquivos gerados pelo gbest do AutodockGPU
    diretorio_gbests = os.path.join(dir_path, "gbest_pdb")
    os.makedirs(diretorio_gbests)
    
    # Diretório para os ligantes separados do arquivo .sdf
    diretorio_lig_split = os.path.join(dir_path, "pdb_split")
    
    # Diretório para os ligantes já preparados / ligantes.pdbqt
    diretorio_ligantes_pdbqt = os.path.join(dir_path, "ligantes_pdbqt")
    os.makedirs(diretorio_ligantes_pdbqt)
    

    return diretorio_macromoleculas,diretorio_dlgs,diretorio_gbests,diretorio_lig_split,diretorio_ligantes_pdbqt

def preparar_ligantes(arquivos_vs, diretorio_lig_split,diretorio_ligantes_pdbqt):
    #caminhos
    pythonsh_path = os.path.expanduser("~/mgltools_x86_64Linux2_1.5.7/bin/pythonsh")
    prep_ligante_path= os.path.expanduser("~/mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py")

    #processo
    arquivo_sdf = os.path.join(settings.MEDIA_ROOT, str(arquivos_vs.ligante))

    command = ["obabel", "-isdf", arquivo_sdf, "-osdf", "--split"]
    executar_comando(command, diretorio_lig_split)

    command = ["rm",arquivo_sdf]
    executar_comando(command, diretorio_lig_split)

    converter_sdf_para_pdb(diretorio_lig_split)
    remover_arquivos_xml(diretorio_lig_split, "*.sdf")

    ligantes_pdb =  listar_arquivos(diretorio_lig_split)

    for ligante_pdb in ligantes_pdb:
        filename_ligante, _ = os.path.splitext(ligante_pdb)
        caminho_ligante_pdb = os.path.join(diretorio_lig_split, ligante_pdb)
        saida = os.path.join(diretorio_ligantes_pdbqt, f"{filename_ligante}.pdbqt")
        command = [pythonsh_path, prep_ligante_path, "-l", caminho_ligante_pdb, "-o", saida]
        executar_comando(command, diretorio_lig_split)



def preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs,diretorio_ligantes_pdbqt,diretorio_macromoleculas,username,nome):
    autodockgpu_path = os.path.expanduser("~/AutoDock-GPU-develop/bin/autodock_gpu_128wi")
    
    receptor_data = {
        'receptor_name': macromolecula.rec,
        'ligante_original': macromolecula.ligante_original,
        'grid_center': macromolecula.gridcenter,
        'grid_size': macromolecula.gridsize,
        'energia_original': macromolecula.energia_orinal,
        'rmsd_redocking': macromolecula.rmsd_redoking,
        'ligantes': []
    }

    data_data = []

    for ligante_pdbqt in ligantes_pdbqt:
        dir_ligante_pdbqt = os.path.join(diretorio_ligantes_pdbqt, ligante_pdbqt)
        filename_ligante, _ = os.path.splitext(ligante_pdbqt)

        r = str(macromolecula.rec_fld)
        dir_path = os.path.join(settings.MEDIA_ROOT, "macromoleculas","comRedocking", f"{macromolecula.rec}")
        rec_maps_fld_path = os.path.join(settings.MEDIA_ROOT, r)
        saida = os.path.join(diretorio_dlgs, f"{filename_ligante}_{macromolecula.rec}")
        

        command = [autodockgpu_path, "--ffile", rec_maps_fld_path, "--lfile", dir_ligante_pdbqt, "--gbest", "1", "--resnam", saida]
        executar_comando(command, dir_path)
        
        diretorio_gbest_ligante_unico = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", nome, "gbest_pdb", filename_ligante)
        os.makedirs(diretorio_gbest_ligante_unico, exist_ok=True)

        bcaminho = os.path.join(settings.MEDIA_ROOT, "macromoleculas","comRedocking", f"{macromolecula.rec}", "best.pdbqt")
        bsaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdbqt")
        shutil.move(bcaminho, bsaida)

        csaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdb")
        command = ["obabel", bsaida, "-O", csaida]
        executar_comando(command, diretorio_gbest_ligante_unico)

        command = ["rm", bsaida]
        executar_comando(command, dir_path)

        sufixos = ['_A.pdb', '_a.pdb', '_ab.pdb', '_bd.pdb', '.pdb']
        for sufixo in sufixos:
            arquivo_path = os.path.join(dir_path, f"{macromolecula.rec}{sufixo}")
            if os.path.exists(arquivo_path):
                shutil.copy2(arquivo_path, diretorio_macromoleculas)
                break
        
        caminho_arquivo = f"{saida}.dlg"

        best_energia, run = extrair_energia_ligacao(caminho_arquivo)

        ligante_data = {
            'ligante_name': filename_ligante,
            'ligante_energia': best_energia,
            'run': run,
        }

        receptor_data['ligantes'].append(ligante_data)
        
        data_data.append({
            'RECEPTOR_NAME': macromolecula.rec,
            'LIGANTE_REDOCKING': macromolecula.ligante_original,
            'ENERGIA_REDOCKING': macromolecula.energia_orinal,
            'LIGANTE_CID': filename_ligante,
            'LIGANTE_MELHOR_ENERGIA': best_energia,
            'RUN': run,
        })

    return receptor_data, data_data
