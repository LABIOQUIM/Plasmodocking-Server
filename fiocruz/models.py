import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Modelo customizado de usuário
class UserCustom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Alterado para UUIDField para consistência de IDs únicos
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    role = models.CharField(
        max_length=255,
        default="USER",
        choices=[('USER', 'User'), ('ADMIN', 'Admin')]  # Exemplo de escolhas restritas
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Data de criação
    updated_at = models.DateTimeField(auto_now=True)  # Data de última modificação

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        db_table = 'users'  # Nome da tabela

# --------------------------------------------------------------------------------------------

def ligante_arquivo(instance, filename):
    return f'plasmodocking/user_{instance.user.username}/{instance.nome}/pdb_split/{filename}'

class ProcessPlasmodocking(models.Model):
    TYPE_CHOICES = [
        ("vivax", "Vivax"),
        ("falciparum", "Falciparum"),
    ]
    STATUS_CHOICES = [
        ("em fila", "Em fila"),
        ("processando", "Processando"),
        ("concluido", "Concluído"),
        ("error", "Erro"),
    ]
    nome = models.CharField(max_length=200)
    user = models.ForeignKey(UserCustom, on_delete=models.CASCADE)
    ligante = models.FileField(upload_to=ligante_arquivo, blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)
    resultado_final = models.TextField(default='Sem resultados')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="em fila")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="falciparum")
    redocking = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} - {self.get_type_display()}"

    class Meta:
        db_table = 'process_plasmodocking'

# --------------------------------------------------------------------------------------------

# Função dinâmica para upload de macromoléculas
def macromolecule_upload_path(instance, filename):
    type_directory = "falciparum" if "Falciparum" in instance._meta.verbose_name else "vivax"
    redocking_directory = "withRedocking" if instance.redocking else "withoutRedocking"
    return f'macromoleculas/{type_directory}/{redocking_directory}/{instance.rec}/{filename}'

# Classe base para Macromoléculas
class Macromolecule(models.Model):
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)
    rec_fld = models.FileField(upload_to=macromolecule_upload_path)

    gridsize = models.CharField(max_length=200, blank=True, null=True)
    gridcenter = models.CharField(max_length=200, blank=True, null=True)

    ligante_original = models.CharField(max_length=200, blank=True, null=True)
    rmsd_redocking = models.CharField(max_length=200, blank=True, null=True)
    energia_original = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        abstract = True

# Macromoléculas Falciparum com redocking
class MacromoleculesFalciparumWithRedocking(Macromolecule):
    redocking = models.BooleanField(default=True)

    class Meta:
        db_table = 'macromolecules_falciparum_with_redocking'

# Macromoléculas Falciparum sem redocking
class MacromoleculesFalciparumWithoutRedocking(Macromolecule):
    ligante_original = None  # Não necessário para este modelo
    rmsd_redocking = None    # Não necessário para este modelo
    energia_original = None  # Não necessário para este modelo
    redocking = models.BooleanField(default=False)

    class Meta:
        db_table = 'macromolecules_falciparum_without_redocking'

# Macromoléculas Vivax com redocking
class MacromoleculesVivaxWithRedocking(Macromolecule):
    redocking = models.BooleanField(default=True)

    class Meta:
        db_table = 'macromolecules_vivax_with_redocking'

# --------------------------------------------------------------------------------------------

def arquivo(instance, filename):
    return f'macroTeste/{instance.processo_name}/{instance.rec}/{filename}'

class MacroPrepare(models.Model):
    processo_name = models.CharField(max_length=200, null=True)
    nome = models.CharField(max_length=200)
    rec = models.CharField(max_length=200)

    receptor_pdb = models.FileField(upload_to=arquivo)
    receptor_pdbqt = models.FileField(upload_to=arquivo, null=True)
    ligante_pdb = models.FileField(upload_to=arquivo, null=True)

    gridsize = models.CharField(max_length=200, blank=True, null=True)
    gridcenter = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        db_table = 'macro_prepare'
