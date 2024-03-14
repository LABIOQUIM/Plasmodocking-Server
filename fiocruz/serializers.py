from django.urls import path, include

from rest_framework import routers, serializers, viewsets

from django.contrib.auth.models import User
from .models import Process_Plasmodocking, UserCustom

class VS_Serializer(serializers.ModelSerializer):
    # Adicione um campo de método para a data formatada
    formatted_data = serializers.SerializerMethodField()

    class Meta:
        model = Process_Plasmodocking
        fields = ['id', 'nome', 'user', 'ligante', 'data', 'redocking', 'status','type', 'formatted_data','resultado_final']

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