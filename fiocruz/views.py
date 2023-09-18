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

class VS_ViewSet(viewsets.ModelViewSet):
    #queryset = Arquivos_virtaulS.objects.all()
    #queryset = Arquivos_virtaulS.objects.filter(status=False)  # Filtrar por status igual a false
    serializer_class = VS_Serializer

    
    def get_queryset(self):
        username = self.request.query_params.get('username')
        user = UserCustom.objects.get(name=username)
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

            dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{arq.user.name}", arq.nome)
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

  

    dir_path = os.path.join(settings.MEDIA_ROOT, "uploads3", f"user_{file.user.name}", file.nome)
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

        texto = """
label=C-affinity	# component label for variable 1
label=A-affinity	# component label for variable 2
label=N-affinity	# component label for variable 3
label=NA-affinity	# component label for variable 4
label=NS-affinity	# component label for variable 5
label=OA-affinity	# component label for variable 6
label=OS-affinity	# component label for variable 7
label=SA-affinity	# component label for variable 8
label=S-affinity	# component label for variable 9
label=H-affinity	# component label for variable 10
label=HD-affinity	# component label for variable 11
label=HS-affinity	# component label for variable 1
label=P-affinity	# component label for variable 2
label=Br-affinity	# component label for variable 3
label=BR-affinity	# component label for variable 4
label=Ca-affinity	# component label for variable 5
label=CA-affinity	# component label for variable 6
label=Cl-affinity	# component label for variable 7
label=CL-affinity	# component label for variable 8
label=F-affinity	# component label for variable 9
label=Fe-affinity	# component label for variable 10
label=FE-affinity	# component label for variable 11
label=I-affinity	# component label for variable 1
label=Mg-affinity	# component label for variable 2
label=MG-affinity	# component label for variable 3
label=Mn-affinity	# component label for variable 4
label=MN-affinity	# component label for variable 5
label=Zn-affinity	# component label for variable 6
label=ZN-affinity	# component label for variable 7
label=He-affinity	# component label for variable 8
label=Li-affinity	# component label for variable 9
label=Be-affinity	# component label for variable 10
label=B-affinity	# component label for variable 1
label=Ne-affinity	# component label for variable 2
label=Na-affinity	# component label for variable 3
label=Al-affinity	# component label for variable 4
label=Si-affinity	# component label for variable 5
label=K-affinity	# component label for variable 6
label=Sc-affinity	# component label for variable 7
label=Ti-affinity	# component label for variable 8
label=V-affinity	# component label for variable 9
label=Co-affinity	# component label for variable 10
label=Ni-affinity	# component label for variable 1
label=Cu-affinity	# component label for variable 2
label=Ga-affinity	# component label for variable 3
label=Ge-affinity	# component label for variable 4
label=As-affinity	# component label for variable 5
label=Se-affinity	# component label for variable 6
label=Kr-affinity	# component label for variable 7
label=Rb-affinity	# component label for variable 8
label=Sr-affinity	# component label for variable 9
label=Y-affinity	# component label for variable 10
label=Zr-affinity	# component label for variable 1
label=Nb-affinity	# component label for variable 2
label=Cr-affinity	# component label for variable 3
label=Tc-affinity	# component label for variable 4
label=Ru-affinity	# component label for variable 5
label=Rh-affinity	# component label for variable 6
label=Pd-affinity	# component label for variable 7
label=Ag-affinity	# component label for variable 8
label=Cd-affinity	# component label for variable 9
label=In-affinity	# component label for variable 10
label=Sn-affinity	# component label for variable 1
label=Sb-affinity	# component label for variable 2
label=Te-affinity	# component label for variable 3
label=Xe-affinity	# component label for variable 4
label=Cs-affinity	# component label for variable 5
label=Ba-affinity	# component label for variable 6
label=La-affinity	# component label for variable 7
label=Ce-affinity	# component label for variable 8
label=Pr-affinity	# component label for variable 9
label=Nd-affinity	# component label for variable 10
label=Pm-affinity	# component label for variable 1
label=Sm-affinity	# component label for variable 2
label=Eu-affinity	# component label for variable 3
label=Gd-affinity	# component label for variable 4
label=Tb-affinity	# component label for variable 5
label=Dy-affinity	# component label for variable 6
label=Ho-affinity	# component label for variable 7
label=Er-affinity	# component label for variable 8
label=Tm-affinity	# component label for variable 9
label=Yb-affinity	# component label for variable 10
label=Lu-affinity	# component label for variable 1
label=Hf-affinity	# component label for variable 2
label=Ta-affinity	# component label for variable 3
label=W-affinity	# component label for variable 4
label=Re-affinity	# component label for variable 5
label=Os-affinity	# component label for variable 6
label=Ir-affinity	# component label for variable 7
label=Pt-affinity	# component label for variable 8
label=Au-affinity	# component label for variable 9
label=Hg-affinity	# component label for variable 10
label=Tl-affinity	# component label for variable 1
label=Pb-affinity	# component label for variable 2
label=Bi-affinity	# component label for variable 3
label=Po-affinity	# component label for variable 4
label=At-affinity	# component label for variable 5
label=Rn-affinity	# component label for variable 6
label=Fr-affinity	# component label for variable 7
label=Ra-affinity	# component label for variable 8
label=Ac-affinity	# component label for variable 9
label=Th-affinity	# component label for variable 10
label=Pa-affinity	# component label for variable 1
label=U-affinity	# component label for variable 2
label=Np-affinity	# component label for variable 3
label=Pu-affinity	# component label for variable 4
label=Am-affinity	# component label for variable 5
label=Cm-affinity	# component label for variable 6
label=Bk-affinity	# component label for variable 7
label=Cf-affinity	# component label for variable 8
label=E-affinity	# component label for variable 9
label=Fm-affinity	# component label for variable 10
label=Electrostatics	# component label for variable 11
label=Desolvation	# component label for variable 12
#
# location of affinity grid files and how to read them
#
variable 1 file=macro.C.map filetype=ascii skip=6
variable 2 file=macro.A.map filetype=ascii skip=6
variable 3 file=macro.N.map filetype=ascii skip=6
variable 4 file=macro.NA.map filetype=ascii skip=6
variable 5 file=macro.NS.map filetype=ascii skip=6
variable 6 file=macro.OA.map filetype=ascii skip=6
variable 7 file=macro.OS.map filetype=ascii skip=6
variable 8 file=macro.SA.map filetype=ascii skip=6
variable 9 file=macro.S.map filetype=ascii skip=6
variable 10 file=macro.H.map filetype=ascii skip=6
variable 11 file=macro.HD.map filetype=ascii skip=6
variable 12 file=macro.HS.map filetype=ascii skip=6
variable 13 file=macro.P.map filetype=ascii skip=6
variable 14 file=macro.Br.map filetype=ascii skip=6
variable 15 file=macro.BR.map filetype=ascii skip=6
variable 16 file=macro.Ca.map filetype=ascii skip=6
variable 17 file=macro.CA.map filetype=ascii skip=6
variable 18 file=macro.Cl.map filetype=ascii skip=6
variable 19 file=macro.CL.map filetype=ascii skip=6
variable 20 file=macro.F.map filetype=ascii skip=6
variable 21 file=macro.Fe.map filetype=ascii skip=6
variable 22 file=macro.FE.map filetype=ascii skip=6
variable 23 file=macro.I.map filetype=ascii skip=6
variable 24 file=macro.Mg.map filetype=ascii skip=6
variable 25 file=macro.MG.map filetype=ascii skip=6
variable 26 file=macro.Mn.map filetype=ascii skip=6
variable 27 file=macro.MN.map filetype=ascii skip=6
variable 28 file=macro.Zn.map filetype=ascii skip=6
variable 29 file=macro.ZN.map filetype=ascii skip=6
variable 30 file=macro.He.map filetype=ascii skip=6
variable 31 file=macro.Li.map filetype=ascii skip=6
variable 32 file=macro.Be.map filetype=ascii skip=6
variable 33 file=macro.B.map filetype=ascii skip=6
variable 34 file=macro.Ne.map filetype=ascii skip=6
variable 35 file=macro.Na.map filetype=ascii skip=6
variable 36 file=macro.Al.map filetype=ascii skip=6
variable 37 file=macro.Si.map filetype=ascii skip=6
variable 38 file=macro.K.map filetype=ascii skip=6
variable 39 file=macro.Sc.map filetype=ascii skip=6
variable 40 file=macro.Ti.map filetype=ascii skip=6
variable 41 file=macro.V.map filetype=ascii skip=6
variable 42 file=macro.Co.map filetype=ascii skip=6
variable 43 file=macro.Ni.map filetype=ascii skip=6
variable 44 file=macro.Cu.map filetype=ascii skip=6
variable 45 file=macro.Ga.map filetype=ascii skip=6
variable 46 file=macro.Ge.map filetype=ascii skip=6
variable 47 file=macro.As.map filetype=ascii skip=6
variable 48 file=macro.Se.map filetype=ascii skip=6
variable 49 file=macro.Kr.map filetype=ascii skip=6
variable 50 file=macro.Rb.map filetype=ascii skip=6
variable 51 file=macro.Sr.map filetype=ascii skip=6
variable 52 file=macro.Y.map filetype=ascii skip=6
variable 53 file=macro.Zr.map filetype=ascii skip=6
variable 54 file=macro.Nb.map filetype=ascii skip=6
variable 55 file=macro.Cr.map filetype=ascii skip=6
variable 56 file=macro.Tc.map filetype=ascii skip=6
variable 57 file=macro.Ru.map filetype=ascii skip=6
variable 58 file=macro.Rh.map filetype=ascii skip=6
variable 59 file=macro.Pd.map filetype=ascii skip=6
variable 60 file=macro.Ag.map filetype=ascii skip=6
variable 61 file=macro.Cd.map filetype=ascii skip=6
variable 62 file=macro.In.map filetype=ascii skip=6
variable 63 file=macro.Sn.map filetype=ascii skip=6
variable 64 file=macro.Sb.map filetype=ascii skip=6
variable 65 file=macro.Te.map filetype=ascii skip=6
variable 66 file=macro.Xe.map filetype=ascii skip=6
variable 67 file=macro.Cs.map filetype=ascii skip=6
variable 68 file=macro.Ba.map filetype=ascii skip=6
variable 69 file=macro.La.map filetype=ascii skip=6
variable 70 file=macro.Ce.map filetype=ascii skip=6
variable 71 file=macro.Pr.map filetype=ascii skip=6
variable 72 file=macro.Nd.map filetype=ascii skip=6
variable 73 file=macro.Pm.map filetype=ascii skip=6
variable 74 file=macro.Sm.map filetype=ascii skip=6
variable 75 file=macro.Eu.map filetype=ascii skip=6
variable 76 file=macro.Gd.map filetype=ascii skip=6
variable 77 file=macro.Tb.map filetype=ascii skip=6
variable 78 file=macro.Dy.map filetype=ascii skip=6
variable 79 file=macro.Ho.map filetype=ascii skip=6
variable 80 file=macro.Er.map filetype=ascii skip=6
variable 81 file=macro.Tm.map filetype=ascii skip=6
variable 82 file=macro.Yb.map filetype=ascii skip=6
variable 83 file=macro.Lu.map filetype=ascii skip=6
variable 84 file=macro.Hf.map filetype=ascii skip=6
variable 85 file=macro.Ta.map filetype=ascii skip=6
variable 86 file=macro.W.map filetype=ascii skip=6
variable 87 file=macro.Re.map filetype=ascii skip=6
variable 88 file=macro.Os.map filetype=ascii skip=6
variable 89 file=macro.Ir.map filetype=ascii skip=6
variable 90 file=macro.Pt.map filetype=ascii skip=6
variable 91 file=macro.Au.map filetype=ascii skip=6
variable 92 file=macro.Hg.map filetype=ascii skip=6
variable 93 file=macro.Tl.map filetype=ascii skip=6
variable 94 file=macro.Pb.map filetype=ascii skip=6
variable 95 file=macro.Bi.map filetype=ascii skip=6
variable 96 file=macro.Po.map filetype=ascii skip=6
variable 97 file=macro.At.map filetype=ascii skip=6
variable 98 file=macro.Rn.map filetype=ascii skip=6
variable 99 file=macro.Fr.map filetype=ascii skip=6
variable 100 file=macro.Ra.map filetype=ascii skip=6
variable 101 file=macro.Ac.map filetype=ascii skip=6
variable 102 file=macro.Th.map filetype=ascii skip=6
variable 103 file=macro.Pa.map filetype=ascii skip=6
variable 104 file=macro.U.map filetype=ascii skip=6
variable 105 file=macro.Np.map filetype=ascii skip=6
variable 106 file=macro.Pu.map filetype=ascii skip=6
variable 107 file=macro.Am.map filetype=ascii skip=6
variable 108 file=macro.Cm.map filetype=ascii skip=6
variable 109 file=macro.Bk.map filetype=ascii skip=6
variable 110 file=macro.Cf.map filetype=ascii skip=6
variable 111 file=macro.E.map filetype=ascii skip=6
variable 112 file=macro.Fm.map filetype=ascii skip=6
variable 113 file=macro.e.map filetype=ascii skip=6
variable 114 file=macro.d.map filetype=ascii skip=6
        """
        
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