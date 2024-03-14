from django.contrib.auth import authenticate
import os
import shutil
import subprocess
import random
from fiocruz.utils.functions import extrair_menor_rmsd
from .models import Process_Plasmodocking, Macromoleculas_virtaulS, UserCustom, Macro_Prepare, Macromoleculas_Sem_Redocking
from rest_framework import viewsets, generics
from django.http import FileResponse, HttpResponse, JsonResponse 
from .serializers import VS_Serializer, UserCustomSerializer
from .tasks import plasmodocking_SR, prepare_macro_SemRedocking, prepare_macro_ComRedocking,plasmodocking_CR
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render

from .util import (
    textfld,
)

class CreateUserView(generics.CreateAPIView):
    queryset = UserCustom.objects.all()
    serializer_class = UserCustomSerializer

#-----------------------------------------------------------------------------------------------------------------

class AuthenticateUser(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            # Buscar o usuário pelo e-mail
            user = UserCustom.objects.get(email=email)
            
            # Verificar se a senha está correta
            if user.check_password(password):
                # Se a senha estiver correta, gerar token de acesso
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserCustomSerializer(user).data
                })
            else:
                # Senha incorreta
                return Response({'error': 'Invalid Credentials. Password invalid'}, status=status.HTTP_401_UNAUTHORIZED)
        except UserCustom.DoesNotExist:
            # Usuário não encontrado
            return Response({'error': 'Invalid Credentials. User not found'}, status=status.HTTP_401_UNAUTHORIZED)


class GetUserDetails(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        user = UserCustom.objects.filter(email=email).first()
        print(email)

        if user:
            return Response(UserCustomSerializer(user).data)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

#-----------------------------------------------------------------------------------------------------------------
class VS_ViewSet(viewsets.ModelViewSet):
    #queryset = Process_Plasmodocking.objects.all()
    #queryset = Process_Plasmodocking.objects.filter(status=False)  # Filtrar por status igual a false
    serializer_class = VS_Serializer

    
    def get_queryset(self):
        username = self.request.query_params.get('username')
        user = UserCustom.objects.get(username=username)
        queryset = Process_Plasmodocking.objects.filter(user=user)
        return queryset
    

def get_resultado(request, idItem):
    if request.method == 'GET':
        try:
            arq = Process_Plasmodocking.objects.get(id=idItem)

            # Use o serializer para serializar o objeto
            serializer = VS_Serializer(arq)

            return JsonResponse({'dados': serializer.data})
        except Process_Plasmodocking.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
      
def api_delete(request, idItem):
    if request.method == 'DELETE':
        try:
            arq = Process_Plasmodocking.objects.get(id=idItem)
            arq.delete()

            dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{arq.user.username}", arq.nome)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    #subprocess.run(["rm", "-rf", dir_path], check=True)
                except subprocess.CalledProcessError as e:
                    return JsonResponse(f"Ocorreu um erro ao excluir o diretório: {e.stderr}")

            return JsonResponse({'message': 'Arquivo apagado com sucesso!'})
        except Process_Plasmodocking.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
    

def download_file(request, id):
    # Recupere o objeto Process_Plasmodocking com base no ID
    file = Process_Plasmodocking.objects.get(id=id)

    dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{file.user.username}", file.nome)
    zip_path = os.path.join(dir_path, f"{file.nome}.zip")
  
    if os.path.exists(zip_path):
        # Retornando o arquivo para download
        response = FileResponse(open(zip_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={file.nome}.zip'
        return response
    else:
        return HttpResponse("O arquivo 2 não foi encontrado.")
    
def generate_unique_id():
    while True:
        new_id = random.randint(1, 1000000)  # Escolha o intervalo apropriado para os IDs
        if not Macromoleculas_virtaulS.objects.filter(id=new_id).exists():
            return new_id
        
def generate_unique_id_SR():
    while True:
        new_id = random.randint(1, 1000000)  # Escolha o intervalo apropriado para os IDs
        if not Macromoleculas_Sem_Redocking.objects.filter(id=new_id).exists():
            return new_id
        
def macro_save_ComRedocking(request):

    if request.method == 'POST':
        processo_name = request.POST.get('processo_name')
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        gridcenter = request.POST.get('gridcenter')
        gridsize = request.POST.get('gridsize')

        ligante_redocking = request.POST.get('ligante_redocking')
        rmsd_redocking = request.POST.get('rmsd_redocking')
        energia_redocking = request.POST.get('energia_redocking')
        fld_name = request.POST.get('fld_name')
        
        dir = os.path.join("macromoleculas", "comRedocking", rec, fld_name)

        unique_id = generate_unique_id()
        macromolecula = Macromoleculas_virtaulS(id=unique_id,nome=nome, rec=rec, gridcenter=gridcenter,
                                       gridsize=gridsize, rmsd_redoking=rmsd_redocking,
                                       energia_orinal=energia_redocking, ligante_original=ligante_redocking,
                                       rec_fld=dir)
        macromolecula.save()

        dir_processo = os.path.join(settings.MEDIA_ROOT, "macroTeste", processo_name, rec)
        dir_macro = os.path.join(settings.MEDIA_ROOT, "macromoleculas", "comRedocking")
        shutil.copytree(dir_processo, os.path.join(dir_macro, rec))

        return JsonResponse({'message': 'Dados recebidos com sucesso!'})

    return JsonResponse({'message': 'Método não suportado'}, status=405)

def macro_save_SemRedocking(request):

    if request.method == 'POST':
        processo_name = request.POST.get('processo_name')
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        gridcenter = request.POST.get('gridcenter')
        gridsize = request.POST.get('gridsize')

        fld_name = request.POST.get('fld_name')
        
        dir = os.path.join("macromoleculas", "semRedocking", rec, fld_name)

        unique_id = generate_unique_id_SR()
        macromolecula = Macromoleculas_Sem_Redocking(id=unique_id,nome=nome, rec=rec, gridcenter=gridcenter,
                                                gridsize=gridsize, rec_fld=dir)
        macromolecula.save()

        dir_processo = os.path.join(settings.MEDIA_ROOT, "macroTeste", processo_name, rec)
        dir_macro = os.path.join(settings.MEDIA_ROOT, "macromoleculas", "semRedocking")
        shutil.copytree(dir_processo, os.path.join(dir_macro, rec))

        return JsonResponse({'message': 'Macromolecula sem redocking salva com sucesso!'})

    return JsonResponse({'message': 'Método não suportado'}, status=405)

def macro(request):
    if request.method == 'POST':
        processo_name = request.POST.get('processo_name')
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        gridcenter = request.POST.get('gridcenter')
        gridsize = request.POST.get('gridsize')
        
        receptorpdb = request.FILES.get('receptorpdb')
        receptorpdbqt = request.FILES.get('receptorpdbqt')
        ligantepdb = request.FILES.get('ligantepdb')

        macroteste = Macro_Prepare(processo_name=processo_name, nome=nome,rec=rec,gridsize=gridsize,gridcenter=gridcenter,
                                   recptorpdb= receptorpdb, recptorpdbqt= receptorpdbqt, ligantepdb= ligantepdb)

        macroteste.save()

        fld_text, fld_name = prepare_macro_ComRedocking(id_processo=macroteste.id)

        filename_receptor, file_extension2 = ligantepdb.name.split(".")

        filename_ligante, file_extension2 = macroteste.ligantepdb.name.split(".")
        caminho_arquivo = os.path.join(settings.MEDIA_ROOT, f"{filename_ligante}.dlg")

        m_rmsd, energia_menor_rmsd = extrair_menor_rmsd(caminho_arquivo)
        
        return JsonResponse({'message': 'Dados recebidos com sucesso!', 'fld_name':fld_name,
                             'gridcenter': gridcenter, 'gridsize': gridsize,'nome': nome,
                             'rec': rec, 'ligante_redocking': filename_receptor,'rmsd_redocking': m_rmsd,
                             'energia_redocking': energia_menor_rmsd, 'arquivo_fld': fld_text
                             })

    return JsonResponse({'message': 'Método não suportado'}, status=405)


def macro_SR(request):
    if request.method == 'POST':
        processo_name = request.POST.get('processo_name')
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        gridcenter = request.POST.get('gridcenter')
        gridsize = request.POST.get('gridsize')
        
        receptorpdb = request.FILES.get('receptorpdb')
        

        macroteste = Macro_Prepare(processo_name=processo_name, nome=nome,rec=rec,gridsize=gridsize,gridcenter=gridcenter,
                                   recptorpdb= receptorpdb)

        macroteste.save()

        fld_text, fld_name = prepare_macro_SemRedocking(id_processo=macroteste.id)
        
        return JsonResponse({'message': 'Dados recebidos com sucesso!', 'fld_name':fld_name,
                             'gridcenter': gridcenter, 'gridsize': gridsize,'nome': nome,
                             'rec': rec, 'arquivo_fld': fld_text
                             })

    return JsonResponse({'message': 'Método não suportado'}, status=405)

#------------------------------------------------------------------------
def upload_view(request):
    if request.method == 'POST':

        nome = request.POST.get('nome')
        arquivo = request.FILES.get('arquivo')
        username = request.POST.get('username')
        type = request.POST.get('type')  # Assumindo que isso vem corretamente como "vivax" ou "falciparum"
        redocking = request.POST.get('redocking') == 'true'  # Isso captura se "redocking" foi marcado como 'true'
        email_user = request.POST.get('email_user')

        try:
            user = UserCustom.objects.get(username=username)
        except UserCustom.DoesNotExist:
            return JsonResponse({'message': 'Usuário não encontrado'}, status=404)
        
        if Process_Plasmodocking.objects.filter(user=user, nome=nome).exists():
            return JsonResponse({'message': 'Um arquivo com esse nome já existe para esse usuário'}, status=400)

        arquivos_vs = Process_Plasmodocking(nome=nome, ligante=arquivo, user=user, type=type, redocking=redocking, status="em fila")
        arquivos_vs.save()

        #---------------------------------------------------------------------
        # Iniciando a task baseado no tipo de processamento e se redocking é True ou False
        if redocking:
            plasmodocking_CR.delay(username, arquivos_vs.id, email_user)
        else: 
            plasmodocking_SR.delay(username, arquivos_vs.id, email_user)

        return JsonResponse({'message': 'Processo adicionado a fila com sucesso. em breve estará disponivel nos resultados.'})
    else:
        return JsonResponse({'message': 'Método não suportado'}, status=405)
    


def view3d(request, username, nome_process, receptor_name, ligante_code):
    receptor_url = f"{settings.MEDIA_URL}plasmodocking/user_{username}/{nome_process}/macromoleculas/{receptor_name}_A.pdb"
    ligante_url = f"{settings.MEDIA_URL}plasmodocking/user_{username}/{nome_process}/gbest_pdb/{ligante_code}/{ligante_code}_{receptor_name}.pdb"
    
    context = {
        'receptor_url': receptor_url,
        'ligante_url': ligante_url
    }
    return render(request, 'view3d.html', context)

