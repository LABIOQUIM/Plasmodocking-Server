
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers, serializers, viewsets
from fiocruz import views

router = routers.DefaultRouter()
router.register(r'VS_doking2', views.VS_ViewSet, basename='admin')
#router.register(r'VS_doking2', views.VS_ViewSet)
#router.register(r'Testes', views.TesteViewSet)
#router.register(r'VS_doking', views.upload_view)


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('VS_doking/', views.upload_view, name='upload_view'),
    
    path('api_delete/<int:idItem>/', views.api_delete, name='api_delete'),
    
    path('api_download/<int:id>/', views.download_file, name='api_download'),
    path('api/get_resultado/<int:idItem>/', views.get_resultado, name='get_resultado'),

    path('macro/', views.macro, name='macro'),
    

]
