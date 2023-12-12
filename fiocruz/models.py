import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime

# Create your models here.

class UserCustom(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False, null=True, blank=True)
    role = models.CharField(max_length=255, default="USER")

    def __str__(self):
        return self.username
    class Meta:
        db_table = 'users'  # Especifique o nome da tabela
        

def ligante_arquivo(instance, filename):
    return 'plasmodocking/user_{0}/{1}/{2}/{3}'.format(instance.user.username, instance.nome,"pdb_split", filename)

class Arquivos_virtaulS(models.Model):
    nome = models.CharField(max_length=200)
    user = models.ForeignKey(UserCustom, on_delete=models.CASCADE)
    ligante = models.FileField(upload_to=ligante_arquivo,blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)
    resultado_final = models.TextField(default='Sem resultados')
    status = models.BooleanField(default=False)
    type = models.TextField(default="Com Redocking")

    def formatted_data(self):
        return self.data.strftime('%H:%M:%S - %d/%m/%Y')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome

    class Meta:
        db_table = 'Arquivos_virtaulS'  # Especifique o nome da tabela

#Macromoleculas Com Redocking
def arquivo_macro(instance, filename):
    return 'macromoleculas/comRedocking/{0}/{1}'.format(instance.rec, filename)

class Macromoleculas_virtaulS(models.Model):
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)
    rec_fld = models.FileField(upload_to=arquivo_macro)

    ligante_original = models.CharField(max_length=200,blank=True, null=True)
    rmsd_redoking = models.CharField(max_length=200,blank=True, null=True)
    energia_orinal = models.CharField(max_length=200,blank=True, null=True)
    gridsize = models.CharField(max_length=200,blank=True, null=True)
    gridcenter = models.CharField(max_length=200,blank=True, null=True)

    def __str__(self):
            return self.nome


#Macromoleculas Sem redocking
def arquivo_macro_SR(instance, filename):
    return 'macromoleculas/semRedocking/{0}/{1}'.format(instance.rec, filename)

class Macromoleculas_Sem_Redocking(models.Model):
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)
    rec_fld = models.FileField(upload_to=arquivo_macro_SR)

    gridsize = models.CharField(max_length=200,blank=True, null=True)
    gridcenter = models.CharField(max_length=200,blank=True, null=True)

    def __str__(self):
            return self.nome
    class Meta:
        db_table = 'Macromoleculas_Sem_Redocking'



def arquivo(instance, filename):
    return 'macroTeste/{0}/{1}/{2}'.format(instance.processo_name,instance.rec, filename)

class Macro_Prepare(models.Model):
    processo_name = models.CharField(max_length=200, null=True)
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)

    recptorpdb = models.FileField(upload_to=arquivo)
    recptorpdbqt = models.FileField(upload_to=arquivo, null=True)
    ligantepdb = models.FileField(upload_to=arquivo, null=True)

    gridsize = models.CharField(max_length=200,blank=True, null=True)
    gridcenter = models.CharField(max_length=200,blank=True, null=True)

    

    def __str__(self):
            return self.nome
    