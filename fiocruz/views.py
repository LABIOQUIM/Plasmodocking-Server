import glob
import os
import shutil
import subprocess
from .models import Arquivos_virtaulS, Macromoleculas_virtaulS, Testes, UserCustom, Macro_Prepare
from rest_framework import routers, serializers, viewsets
from django.http import FileResponse, HttpResponse, JsonResponse 
from django.contrib.auth.models import User
import json
from .serializers import VS_Serializer
import pandas as pd

from django.conf import settings

from .utils import (
    extrair_energia_ligacao,
    converter_sdf_para_pdb,
    executar_comando,
    remover_arquivos_xml,
    listar_arquivos,
    textfld,
)

class VS_ViewSet(viewsets.ModelViewSet):
    #queryset = Arquivos_virtaulS.objects.all()
    #queryset = Arquivos_virtaulS.objects.filter(status=False)  # Filtrar por status igual a false
    serializer_class = VS_Serializer

    
    def get_queryset(self):
        username = self.request.query_params.get('username')
        user = UserCustom.objects.get(username=username)
        queryset = Arquivos_virtaulS.objects.filter(user=user)
        return queryset
    

def get_resultado(request, idItem):
    if request.method == 'GET':
        try:
            arq = Arquivos_virtaulS.objects.get(id=idItem)

            # Use o serializer para serializar o objeto
            serializer = VS_Serializer(arq)

            return JsonResponse({'dados': serializer.data})
        except Arquivos_virtaulS.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
    
    
def api_delete(request, idItem):
    if request.method == 'DELETE':
        try:
            arq = Arquivos_virtaulS.objects.get(id=idItem)
            arq.delete()

            dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{arq.user.username}", arq.nome)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    #subprocess.run(["rm", "-rf", dir_path], check=True)
                except subprocess.CalledProcessError as e:
                    return JsonResponse(f"Ocorreu um erro ao excluir o diretório: {e.stderr}")

            return JsonResponse({'message': 'Arquivo apagado com sucesso!'})
        except Arquivos_virtaulS.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
    


def download_file(request, id):
    # Recupere o objeto Arquivos_virtaulS com base no ID
    file = Arquivos_virtaulS.objects.get(id=id)

  

    dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{file.user.username}", file.nome)
    zip_path = os.path.join(dir_path, f"{file.nome}.zip")
    # Suponha que 'arquivo' seja um campo FileField ou similar em seu modelo Arquivos_virtaulS.
    # Você pode ajustar essa parte de acordo com sua estrutura de modelo.
    #arquivo = zip_path

    # Configure os cabeçalhos de resposta para iniciar o download do arquivo
    if os.path.exists(zip_path):
        # Retornando o arquivo para download
        response = FileResponse(open(zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={file.nome}.zip'
        return response
    else:
        return HttpResponse("O arquivo 2 não foi encontrado.")

def processar_comando(command, cwd):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return False, stderr.decode()
        return True, None
    except Exception as e:
        return False, str(e)



def macro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        sizex = request.POST.get('sizex')
        sizey = request.POST.get('sizey')
        sizez = request.POST.get('sizez')
        centerx = request.POST.get('centerx')
        centery = request.POST.get('centery')
        centerz = request.POST.get('centerz')
        receptorpdb = request.FILES.get('receptorpdb')
        receptorpdbqt = request.FILES.get('receptorpdbqt')
        ligantepdb = request.FILES.get('ligantepdb')

        macroteste = Macro_Prepare(nome=nome,rec=rec,sizeX=sizex,sizeY=sizey,sizeZ=sizez,
                                   centerX=centerx,centerY=centery,centerZ=centerz,
                                   recptorpdb= receptorpdb, recptorpdbqt= receptorpdbqt, ligantepdb= ligantepdb)

        macroteste.save()
        #---------------------------------------------------------------------
        #caminhos
        autodockgpu_path = str(settings.BASE_DIR)+"/../../AutoDock-GPU-develop/bin/autodock_gpu_128wi"
        pythonsh_path = str(settings.BASE_DIR)+"/../../mgltools_x86_64Linux2_1.5.7/bin/pythonsh"
        prep_ligante_path= str(settings.BASE_DIR)+"/../../mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py"
        prep_gpf_path= str(settings.BASE_DIR)+"/../../mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_gpf4.py"
        autogrid_path= "/home/eduardo/x86_64Linux2/autogrid4"

        #---------------------------------------------------
        #-------------preparação gpf------------------------
        g = 'gridcenter={0},{1},{2}'.format(macroteste.centerX,macroteste.centerY,macroteste.centerZ)
        n = 'npts={0},{1},{2}'.format(macroteste.sizeX,macroteste.sizeY,macroteste.sizeZ)

        dir_path = os.path.join(settings.MEDIA_ROOT, "macroTeste", f"{rec}")
        r = str(macroteste.recptorpdbqt)
        l = str(macroteste.ligantepdb)
        ligante = os.path.join(settings.MEDIA_ROOT, l)
        receptor = os.path.join(settings.MEDIA_ROOT, r)

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
            saida = os.path.join(settings.MEDIA_ROOT, "macroTeste", f"{rec}", f'gridbox{i}.gpf')
            comando = [
                pythonsh_path, prep_gpf_path, "-r", receptor, "-o", saida, "-p", g, "-p", n, "-p", lt
            ]
            comandos.append(comando)

        for comando in comandos:
            success, error_msg = processar_comando(comando, dir_path)
            if not success:
                return HttpResponse(f"Ocorreu um erro: {error_msg}")
            
        
        comando = [pythonsh_path, prep_ligante_path, "-l", ligante]
        success, error_msg = processar_comando(comando, dir_path)
        if not success:
            return HttpResponse(f"Ocorreu um erro: {error_msg}")
            
        #for filename in glob.glob("*.gpf"):
        for i in range(1, 12):
            saida = os.path.join(settings.MEDIA_ROOT, "macroTeste", f"{rec}", f'gridbox{i}.gpf')
            saidaaa = f'gridbox{i}.gpf'
  
            sed_command = f"sed -i '1i\\parameter_file /home/eduardo/x86_64Linux2/AD4_parameters.dat' {saida}"
            subprocess.run(sed_command, shell=True, check=True)

            autogrid_command = f"/home/eduardo/x86_64Linux2/autogrid4 -p {saidaaa} -l gridbox.glg"
            #autogrid_command = f"/home/eduardo/x86_64Linux2/autogrid4 -p {full_path} -l {output_glg}"
            subprocess.run(autogrid_command, shell=True, check=True, cwd=dir_path)

            sed_command = f"sed -i '/# component label for variable 1/,$d' *.maps.fld"
            subprocess.run(sed_command, shell=True, check=True)
        

        file_path = f'/home/eduardo/plasmodocking/media/macroTeste/{rec}/{rec}_a.maps.fld'  # Substitua pelo caminho do seu arquivo
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

        filename_ligante, file_extension2 = receptorpdb.name.split(".")

        texto = textfld()
        
        # Substituindo todas as ocorrências de 'macro' por 'receptor'
        novo_texto = texto.replace("macro", filename_ligante)

        # Imprimindo o texto resultante
        with open(file_path, "a") as arquivo:
            # Escrevendo o novo texto no arquivo
            arquivo.write(novo_texto)

        # Fechando o arquivo
        arquivo.close()

        g = '{0},{1},{2}'.format(macroteste.centerX,macroteste.centerY,macroteste.centerZ)
        n = '{0},{1},{2}'.format(macroteste.sizeX,macroteste.sizeY,macroteste.sizeZ)

        return JsonResponse({'message': 'Dados recebidos com sucesso!', 'gridcenter': g, 'gridsize': n})

    return JsonResponse({'message': 'Método não suportado'}, status=405)




def upload_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        arquivo = request.FILES.get('arquivo')
        username = request.POST.get('username')

        try:
            user = UserCustom.objects.get(username=username)
        except UserCustom.DoesNotExist:
            return JsonResponse({'message': 'Usuário não encontrado'}, status=404)
        
        # Verificar se já existe um objeto com o mesmo usuário e nome
        if Arquivos_virtaulS.objects.filter(user=user, nome=nome).exists():
            return JsonResponse({'message': 'Um arquivo com esse nome já existe para esse usuário'}, status=400)

        
        arquivos_vs = Arquivos_virtaulS(nome=nome, ligante=arquivo, user=user)
        arquivos_vs.save()

        #---------------------------------------------------------------------
        #caminhos
        autodockgpu_path = str(settings.BASE_DIR)+"/../../AutoDock-GPU-develop/bin/autodock_gpu_128wi"
        pythonsh_path = str(settings.BASE_DIR)+"/../../mgltools_x86_64Linux2_1.5.7/bin/pythonsh"
        prep_ligante_path= str(settings.BASE_DIR)+"/../../mgltools_x86_64Linux2_1.5.7/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py"

        #---------------------------------------------------------------------
        # criar pastas do usuario 
        
        dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome)
        
        #diretorio para as macromolecula/receptors utilizados
        direto_macromoleculas = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "macromoleculas")
        os.makedirs(direto_macromoleculas)
        
        #direotio para os arquivos .dlgs gerados no processo 
        direto_dlgs = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "arquivos_dlgs")
        os.makedirs(direto_dlgs)
        
        #diretorio para os arquivos gerados pelo gbest do AutodockGPU
        direto_gbests = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "gbest_pdb")
        os.makedirs(direto_gbests)
        
        #diretorio para os ligantes seprados do arquivo .sdf
        direto_ling_split = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "pdb_split")
        
        #diretorio para os ligantes ja preparados / ligantes.pdbqt
        diretorio_ligantes_pdbqt = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "ligantes_pdbqt")
        os.makedirs(diretorio_ligantes_pdbqt)

        #---------------------------------------------------------------------
        #preparação ligante
        lig = str(arquivos_vs.ligante)
        arquivo_sdf = settings.MEDIA_ROOT+lig

        command = ["obabel", "-isdf", arquivo_sdf, "-osdf", "--split"]
        executar_comando(command, direto_ling_split)

        command = ["rm",arquivo_sdf]
        executar_comando(command, direto_ling_split)

        converter_sdf_para_pdb(direto_ling_split)
       
        remover_arquivos_xml(direto_ling_split, "*.sdf")

        ligantes_pdb =  listar_arquivos(direto_ling_split)
        print(ligantes_pdb)

        for ligante_pdb in ligantes_pdb:
           
            filename_ligante, file_extension2 = ligante_pdb.split(".")

            caminho_ligante_pdb = os.path.join(direto_ling_split,ligante_pdb)
            
            saida = os.path.join(dir_path,"ligantes_pdbqt",f"{filename_ligante}.pdbqt")
            command = [pythonsh_path, prep_ligante_path, "-l", caminho_ligante_pdb, "-o", saida]

            executar_comando(command, direto_ling_split)

            ligantes_pdbqt = listar_arquivos(diretorio_ligantes_pdbqt)

        #---------------------------------------------------------------------
        #execução do AutodockGPU
        macromoleculas = Macromoleculas_virtaulS.objects.all()
       
        i = 1
        data = []
        datacsv = []
        for macromolecula in macromoleculas:
            receptor_data = {
            'receptor_name': macromolecula.rec,
            'ligante_original': macromolecula.ligante_original,
            'grid_center': macromolecula.gridcenter,
            'grid_size': macromolecula.gridsize,
            'energia_original': macromolecula.energia_orinal,
            'rmsd_redocking': macromolecula.rmsd_redoking,
            'ligantes': []  # Lista para armazenar os ligantes associados a este receptor
        }
            for ligante_pdbqt in ligantes_pdbqt:

                dir_ligante_pdbqt = os.path.join(diretorio_ligantes_pdbqt, ligante_pdbqt)

                filename_ligante, _ = ligante_pdbqt.split(".")
                r = str(macromolecula.rec_fld)
                dir_path = os.path.join(settings.MEDIA_ROOT, "macromoleculas_virtualS", f"{macromolecula.rec}")
                rec_maps_fld_path = os.path.join(settings.MEDIA_ROOT, r)
                saida = os.path.join(direto_dlgs, f"{filename_ligante}_{macromolecula.rec}")
                print(rec_maps_fld_path)
                
                command = [autodockgpu_path, "--ffile", rec_maps_fld_path, "--lfile", dir_ligante_pdbqt, "--gbest", "1", "--resnam", saida]

                executar_comando(command, dir_path)
            
                if os.path.exists(f"{dir_path}/{macromolecula.rec}_A.pdb"):
                    shutil.copy2(f"{dir_path}/{macromolecula.rec}_A.pdb", direto_macromoleculas)

                elif os.path.exists(f"{dir_path}/{macromolecula.rec}_a.pdb"):
                    shutil.copy2(f"{dir_path}/{macromolecula.rec}_a.pdb", direto_macromoleculas)
                
                elif os.path.exists(f"{dir_path}/{macromolecula.rec}_ab.pdb"):
                    shutil.copy2(f"{dir_path}/{macromolecula.rec}_ab.pdb", direto_macromoleculas)

                elif os.path.exists(f"{dir_path}/{macromolecula.rec}.pdb"):
                    shutil.copy2(f"{dir_path}/{macromolecula.rec}.pdb", direto_macromoleculas)

                

                #---------separar os arquivos gbest--------------------
                diretorio_gbest_ligante_unico = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome, "gbest_pdb", filename_ligante)
                os.makedirs(diretorio_gbest_ligante_unico, exist_ok=True)
                bcaminho = os.path.join(settings.MEDIA_ROOT, "macromoleculas_virtualS", f"{macromolecula.rec}", "best.pdbqt")
                bsaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdbqt")
                shutil.move(bcaminho, bsaida)

                #-----------------------------------------------------------
                #-------------------converter os pdbqr pra pdb--------------
                csaida = os.path.join(diretorio_gbest_ligante_unico, f"{filename_ligante}_{macromolecula.rec}.pdb")
                command = ["obabel", bsaida, "-O", csaida]
                executar_comando(command, diretorio_gbest_ligante_unico)

                command = ["rm", bsaida]
                executar_comando(command, dir_path)

                #-------------------------leitura arquivo--------------------------
                caminho_arquivo = f"{saida}.dlg"

                best_energia, run= extrair_energia_ligacao(caminho_arquivo)
                ligante_data = {
                'ligante_name': filename_ligante,
                'ligante_energia': best_energia,
                'run': run,
                }

                data_data = {
                    'RECEPTOR_NAME': macromolecula.rec,
                    'LIGANTE_REDOCKING': macromolecula.ligante_original,
                    'ENERGIA_REDOCKING' : macromolecula.energia_orinal,
                    'LIGANTE_CID': filename_ligante,
                    'LIGANTE_MELHOR_ENERGIA': best_energia,
                    'RUN': run,
                }
                receptor_data['ligantes'].append(ligante_data)

                datacsv.append(data_data)

                
            #  
            i= i+1
            data.append(receptor_data)
            
        dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome,"arquivos_dlgs")
        remover_arquivos_xml(dir_path, "*.xml")
        
        #----------------zip file---------------

        dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}")
        command = ["zip", "-r", nome+"/"+nome+".zip", nome]
        executar_comando(command, dir_path)


        
        json_data = json.dumps(data, indent=4)  # Serializa os dados em JSON formatado
        json_dataaa = json.dumps(data, indent=4)  # Serializa os dados em JSON formatado
      
        # Especifique o caminho e nome do arquivo onde você deseja salvar o JSON
        file_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome,"teste.json")
        
        with open(file_path, 'w') as json_file:
            json_file.write(json_data)

        arquivos_vs.status = True
        arquivos_vs.resultado_final = json_data
        arquivos_vs.resultadoJson = json_data
        arquivos_vs.save()

        file_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{username}", nome)

        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)
        csv_file_path = os.path.join(file_path, 'dados.csv')
        df.to_csv(csv_file_path, index=False)

        dfdf = pd.DataFrame(datacsv)

        # Use o sep para definir o separador como ';'
        csv_file_path = os.path.join(file_path, 'dadostab.csv')
        dfdf.to_csv(csv_file_path, sep=';', index=False)

        return JsonResponse({'message': 'Dados recebidos com sucesso!'})

    return JsonResponse({'message': 'Método não suportado'}, status=405)

#------------------------------------------------------------------------
