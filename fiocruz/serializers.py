from django.urls import path, include

from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import User
from .models import Arquivos_virtaulS

class VS_Serializer(serializers.ModelSerializer):
    # Adicione um campo de método para a data formatada
    formatted_data = serializers.SerializerMethodField()

    class Meta:
        model = Arquivos_virtaulS
        fields = ['id', 'nome', 'user', 'ligante', 'data', 'resultado_final', 'status','type', 'formatted_data']

    def get_formatted_data(self, obj):
        # Formate a data como desejado
        return obj.data.strftime('%H:%M:%S - %d/%m/%Y')