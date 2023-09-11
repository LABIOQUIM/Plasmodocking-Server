import glob
import os
import shutil
import subprocess
from .models import Arquivos_virtaulS, Macromoleculas_virtaulS, Testes, UserCustom
from rest_framework import routers, serializers, viewsets
from django.http import FileResponse, HttpResponse, JsonResponse 
from django.contrib.auth.models import User
import json
from .serializers import VS_Serializer
import pandas as pd

from django.conf import settings

class VS_ViewSet(viewsets.ModelViewSet):
    #queryset = Arquivos_virtaulS.objects.all()
    #queryset = Arquivos_virtaulS.objects.filter(status=False)  # Filtrar por status igual a false
    serializer_class = VS_Serializer

    
    def get_queryset(self):
        username = self.request.query_params.get('username')
        user = UserCustom.objects.get(name=username)
        queryset = Arquivos_virtaulS.objects.filter(user=user)
        return queryset
    
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

    file.user.username

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

def api_cadastro(request):

    if request.method == 'POST':
        data = json.loads(request.body)

        name=data['nome_usuario']
        email=data['email']
        password=data['password']
        firstname=data['nome']

        user_exists = UserCustom.objects.filter(name=name).exists()
        if(user_exists):
           return JsonResponse({'message': 'Ja tem um usuario com esse Username.'}, status=400) 
        
        user_exists = UserCustom.objects.filter(email=email).exists()
        if(user_exists):
           return JsonResponse({'message': 'Ja tem um usuario com esse email.'}, status=400) 


        newuser = UserCustom(name=name, email=email, firstname=firstname, password=password)
        newuser.save()
        
        
        return JsonResponse({'message': 'Usuário cadastrado com sucesso!'})
    return JsonResponse({'message': 'Método não permitido'}, status=405)


def api_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username_to_check = data['username']
        password = data['Password']
        
        
        user_exists = User.objects.filter(username=username_to_check).exists()

        if user_exists:
            return JsonResponse({'user_id': user_exists.id})
        
        else:
            return JsonResponse({'mensage': 'false'}, status=401)
    return JsonResponse({'message': 'Método não permitido'}, status=405)



def upload_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        arquivo = request.FILES.get('arquivo')
        username = request.POST.get('username')

        try:
            user = UserCustom.objects.get(name=username)
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
                receptor_data['ligantes'].append(ligante_data)


                
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

        return JsonResponse({'message': 'Dados recebidos com sucesso!'})

    return JsonResponse({'message': 'Método não suportado'}, status=405)

#------------------------------------------------------------------------










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


def converter_sdf_para_pdb(diretorio_sdf):
    arquivos_sdf = glob.glob(os.path.join(diretorio_sdf, "*.sdf"))
    if not arquivos_sdf:
        return False

    comando = ["obabel", "-isdf"] + arquivos_sdf + ["-opdb", "-O*.pdb"]
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