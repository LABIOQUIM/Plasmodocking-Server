import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


# Create your models here.

class UserCustom(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, max_length=255)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True)
    active = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    role = models.CharField(max_length=50, default='USER')

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users'  # Especifique o nome da tabela

def ligante_arquivo(instance, filename):
    return 'uploads3/user_{0}/{1}/{2}/{3}'.format(instance.user.username, instance.nome,"pdb_split", filename)

class Arquivos_virtaulS(models.Model):


    nome = models.CharField(max_length=200)

    user = models.ForeignKey(UserCustom, on_delete=models.CASCADE)

    ligante = models.FileField(upload_to=ligante_arquivo,blank=True, null=True)

    data = models.DateTimeField(auto_now_add=True)  
    
    resultado_final = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'Arquivos_virtaulS'  # Especifique o nome da tabela



class Macromoleculas_virtaulS(models.Model):
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)
    rec_fld = models.FileField(upload_to='macromoleculas_virtualS')

    ligante_original = models.CharField(max_length=200,blank=True, null=True)
    rmsd_redoking = models.CharField(max_length=200,blank=True, null=True)
    energia_orinal = models.CharField(max_length=200,blank=True, null=True)
    gridsize = models.CharField(max_length=200,blank=True, null=True)
    gridcenter = models.CharField(max_length=200,blank=True, null=True)

    def __str__(self):
            return self.nome
    
class Testes(models.Model):
    nome = models.CharField(max_length=200)