from django.urls import path, include

from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import User
from .models import Arquivos_virtaulS

class VS_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Arquivos_virtaulS
        fields = ['id', 'nome', 'user', 'ligante','data', 'resultado_final','status']

       