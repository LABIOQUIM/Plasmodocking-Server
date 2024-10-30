from django.contrib.auth import authenticate
import os
import shutil
import subprocess
import random
from fiocruz.utils.functions import extrair_menor_rmsd
from .models import ProcessPlasmodocking, MacromoleculesFalciparumWithRedocking, UserCustom, MacroPrepare, MacromoleculesFalciparumWithoutRedocking
from rest_framework import viewsets, generics
from django.http import FileResponse, HttpResponse, JsonResponse 
from .serializers import ProcessPlasmodockingSerializer, VS_Serializer, UserCustomSerializer
from .tasks import plasmodocking_SR, prepare_macro_SemRedocking, prepare_macro_ComRedocking,plasmodocking_CR
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
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
        print(email)
        print(password)
        try:
            # Buscar o usuário pelo e-mail
            # user = UserCustom.objects.get(email=email)
            
            try:
                user = UserCustom.objects.get(email=email)
            except UserCustom.DoesNotExist:
                return Response({'message': f'Usuário não encontrado: {email}'}, status=status.HTTP_404_NOT_FOUND)
                
            
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

def get_resultado(request, idItem):
    if request.method == 'GET':
        try:
            arq = ProcessPlasmodocking.objects.get(id=idItem)

            # Use o serializer para serializar o objeto
            serializer = VS_Serializer(arq)

            return JsonResponse({'dados': serializer.data})
        except ProcessPlasmodocking.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
      
def api_delete(request, idItem):
    if request.method == 'DELETE':
        try:
            arq = ProcessPlasmodocking.objects.get(id=idItem)
            arq.delete()

            dir_path = os.path.join(settings.MEDIA_ROOT, "plasmodocking", f"user_{arq.user.username}", arq.nome)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    #subprocess.run(["rm", "-rf", dir_path], check=True)
                except subprocess.CalledProcessError as e:
                    return JsonResponse(f"Ocorreu um erro ao excluir o diretório: {e.stderr}")

            return JsonResponse({'message': 'Arquivo apagado com sucesso!'})
        except ProcessPlasmodocking.DoesNotExist:
            return JsonResponse({'message': 'Item não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método não permitido'}, status=405)
    

def download_file(request, id):
    # Recupere o objeto ProcessPlasmodocking com base no ID
    file = ProcessPlasmodocking.objects.get(id=id)

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
        if not MacromoleculesFalciparumWithRedocking.objects.filter(id=new_id).exists():
            return new_id
        
def generate_unique_id_SR():
    while True:
        new_id = random.randint(1, 1000000)  # Escolha o intervalo apropriado para os IDs
        if not MacromoleculesFalciparumWithoutRedocking.objects.filter(id=new_id).exists():
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
        macromolecula = MacromoleculesFalciparumWithRedocking(id=unique_id,nome=nome, rec=rec, gridcenter=gridcenter,
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
        macromolecula = MacromoleculesFalciparumWithoutRedocking(id=unique_id,nome=nome, rec=rec, gridcenter=gridcenter,
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

        macroteste = MacroPrepare(processo_name=processo_name, nome=nome,rec=rec,gridsize=gridsize,gridcenter=gridcenter,
                                   recptorpdb= receptorpdb, recptorpdbqt= receptorpdbqt, ligantepdb= ligantepdb)

        macroteste.save()

        prepare_macro_ComRedocking.delay(id_processo=macroteste.id)

        
        
        return JsonResponse({'message': 'Dados recebidos com sucesso!'})

    return JsonResponse({'message': 'Método não suportado'}, status=405)

def macro_SR(request):
    if request.method == 'POST':
        processo_name = request.POST.get('processo_name')
        nome = request.POST.get('nome')
        rec = request.POST.get('rec')
        gridcenter = request.POST.get('gridcenter')
        gridsize = request.POST.get('gridsize')
        
        receptorpdb = request.FILES.get('receptorpdb')
        

        macroteste = MacroPrepare(processo_name=processo_name, nome=nome,rec=rec,gridsize=gridsize,gridcenter=gridcenter,
                                   recptorpdb= receptorpdb)

        macroteste.save()

        fld_text, fld_name = prepare_macro_SemRedocking(id_processo=macroteste.id)
        
        return JsonResponse({'message': 'Dados recebidos com sucesso!', 'fld_name':fld_name,
                             'gridcenter': gridcenter, 'gridsize': gridsize,'nome': nome,
                             'rec': rec, 'arquivo_fld': fld_text
                             })

    return JsonResponse({'message': 'Método não suportado'}, status=405)


    

def view3d(request, username, nome_process, receptor_name, ligante_code):
    dir_path_receptor = os.path.join(settings.MEDIA_ROOT, f"plasmodocking/user_{username}/{nome_process}/macromoleculas")
    dir_path_ligante = os.path.join(settings.MEDIA_ROOT, f"plasmodocking/user_{username}/{nome_process}/gbest_pdb/{ligante_code}")
    
    # Tentativas de sufixos para o arquivo do receptor
    sufixos_receptor = ['_A.pdb', '_a.pdb', '_ab.pdb', '_bd.pdb', '.pdb']
    receptor_path = None
    for sufixo in sufixos_receptor:
        temp_path = os.path.join(dir_path_receptor, f"{receptor_name}{sufixo}")
        if os.path.exists(temp_path):
            receptor_path = temp_path
            break
            
    # Se nenhum arquivo for encontrado, handle o caso conforme necessário
    if receptor_path is None:
        raise FileNotFoundError(f"Arquivo do receptor {receptor_name} não encontrado.")
    
    # Para o ligante, a lógica permanece a mesma
    ligante_path = os.path.join(dir_path_ligante, f"{ligante_code}_{receptor_name}.pdb")
    if not os.path.exists(ligante_path):
        raise FileNotFoundError(f"Arquivo do ligante {ligante_code} não encontrado.")
    
    with open(receptor_path, 'r') as file:
        receptor_data = file.read()
    with open(ligante_path, 'r') as file:
        ligante_data = file.read()
    
    context = {
        'receptor_data': receptor_data,
        'ligante_data': ligante_data
    }
    return render(request, 'view3d.html', context)  


class ProcessPlasmodockingViewSet(viewsets.ModelViewSet):
    queryset = ProcessPlasmodocking.objects.all()
    serializer_class = ProcessPlasmodockingSerializer
    parser_classes = [MultiPartParser, FormParser]  # Para aceitar arquivos multipart

    @action(detail=False, methods=['get'], url_path='by-user')
    def by_user(self, request):
        username = request.query_params.get('username', None)
        if username is not None:
            try:
                user = UserCustom.objects.get(username=username)
            except UserCustom.DoesNotExist:
                return Response({"message": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)
            queryset = ProcessPlasmodocking.objects.filter(user=user)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Parâmetro 'username' é necessário."}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        data = request.data
        username = data.get('username')
        nome = data.get('nome')
        arquivo = request.FILES.get('arquivo')
        type = data.get('type')  # Tipo: 'vivax' ou 'falciparum'
        redocking = data.get('redocking', True)  # Será passado como booleano
        email_user = data.get('email_user')

        # Converter redocking para booleano
        redocking = True if redocking in ['true', 'True', True] else False

        # Verificar se o usuário existe
        try:
            user = UserCustom.objects.get(username=username)
        except UserCustom.DoesNotExist:
            return Response({'message': 'Usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar se já existe um processo com esse nome para o usuário
        if ProcessPlasmodocking.objects.filter(user=user, nome=nome).exists():
            return Response({'message': 'Um processo com esse nome já existe para este usuário'}, status=status.HTTP_400_BAD_REQUEST)

        # Criar um novo processo
        arquivos_vs = ProcessPlasmodocking(
            nome=nome,
            ligante=arquivo,
            user=user,
            type=type,
            redocking=redocking,
            status="em fila"
        )
        arquivos_vs.save()

        plasmodocking_CR.delay(username, arquivos_vs.id, user.email)
        
        # Serializar e retornar a resposta
        serializer = self.get_serializer(arquivos_vs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)