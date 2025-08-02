from django.urls import path
from . import views

app_name = 'integrity'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('documentos/upload/', views.upload_documento, name='upload_documento'),
    path('documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),
    path('documentos/<int:documento_id>/permissoes/', views.gerenciar_permissoes, name='gerenciar_permissoes'),
    path('documentos/<int:documento_id>/assinar/', views.assinar_documento, name='assinar_documento'),
]