import os
from pathlib import Path
import shutil

from django.conf import settings

from .functions import (
    extrair_energia_ligacao,
    converter_sdf_para_pdb,
    executar_comando,
    remover_arquivos_xml,
    listar_arquivos,
    extrair_menor_rmsd,
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

def preparar_ligantes(arquivos_vs, diretorio_lig_split, diretorio_ligantes_pdbqt):
    #caminhos
    pythonsh_path = os.path.expanduser("/home/autodockgpu/mgltools_x86_64Linux2_1.5.7/bin/pythonsh")
    prep_ligante_path= os.path.expanduser("/home/autodockgpu/mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py")
    obabel_path= os.path.expanduser("/usr/bin/obabel")

    #processo
    arquivo_sdf = os.path.join(settings.MEDIA_ROOT, str(arquivos_vs.ligante))

    command = [obabel_path, "-isdf", arquivo_sdf, "-osdf", "--split"]
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

def preparar_dados_receptor(macromolecula, ligantes_pdbqt, diretorio_dlgs, diretorio_ligantes_pdbqt, diretorio_macromoleculas, username, nome, type, redocking):
    autodockgpu_path = os.path.expanduser("/home/autodockgpu/AutoDock-GPU/bin/autodock_gpu_128wi")
    obabel_path = os.path.expanduser("/usr/bin/obabel")
    
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
        command = [autodockgpu_path, "--ffile", rec_maps_fld_path, "--lfile", dir_ligante_pdbqt, "--gbest", "1", "--resnam", saida]
        print(f"Command run autodock: {command}")
        executar_comando(command, dir_path)
        
        # Configura caminho para o arquivo de melhor ligação (gbest)
        diretorio_gbest_ligante_unico = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{username}", nome, "gbest_pdb", filename_ligante)
        os.makedirs(diretorio_gbest_ligante_unico, exist_ok=True)
        
        #==================================================
        # Padrões de arquivos possíveis: "best.pdbqt" ou "<ligante>-best.pdbqt"
        padroes_arquivos = [
            os.path.join(dir_path, "best.pdbqt"),
            os.path.join(dir_path, f"{Path(filename_ligante).stem}-best.pdbqt"),
            os.path.join(diretorio_dlgs, "best.pdbqt"),
            os.path.join(diretorio_dlgs, f"{Path(filename_ligante).stem}_{macromolecula.rec}-best.pdbqt"),
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

    return receptor_data, data_data
