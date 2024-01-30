from django.urls import path, include

from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import User
from .models import Arquivos_virtaulS, UserCustom

class VS_Serializer(serializers.ModelSerializer):
    # Adicione um campo de método para a data formatada
    formatted_data = serializers.SerializerMethodField()

    class Meta:
        model = Arquivos_virtaulS
        fields = ['id', 'nome', 'user', 'ligante', 'data', 'resultado_final', 'status','type', 'formatted_data']

    def get_formatted_data(self, obj):
        # Formate a data como desejado
        return obj.data.strftime('%H:%M:%S - %d/%m/%Y')
    

class UserCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCustom
        fields = ['id', 'name', 'email', 'username', 'password', "active", "deleted", "role", "created_at", "updated_at"]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserCustom.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            name=validated_data['name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user