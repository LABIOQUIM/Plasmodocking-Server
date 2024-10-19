from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from fiocruz import views

router = routers.DefaultRouter()
router.register(r'Plasmodocking/back/process-plasmodocking', views.ProcessPlasmodockingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('Plasmodocking/back/admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('Plasmodocking/back/api_delete/<int:idItem>/', views.api_delete, name='api_delete'),
    path('Plasmodocking/back/api_download/<int:id>/', views.download_file, name='api_download'),
    path('Plasmodocking/back/get_resultado/<int:idItem>/', views.get_resultado, name='get_resultado'),
    path('macro/', views.macro, name='macro'),
    path('macro_SR/', views.macro_SR, name='macro_SR'),
    path('macro_ComRedocking_save/', views.macro_save_ComRedocking, name='macro_save_CR'),
    path('macro_SemRedocking_save/', views.macro_save_SemRedocking, name='macro_save_SR'),
    path('Plasmodocking/back/create-user/', views.CreateUserView.as_view(), name='create-user'),
    path('Plasmodocking/back/authenticate', views.AuthenticateUser.as_view(), name='authenticate'),
    path('Plasmodocking/back/user', views.GetUserDetails.as_view(), name='get_user_details'),
    path('Plasmodocking/back/view3d/<str:username>/<str:nome_process>/<str:receptor_name>/<str:ligante_code>/', views.view3d, name='view3d'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
