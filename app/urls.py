"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from integrity import views  # Importe suas views do app integrity

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URL raiz apontando para a view de login
    path('', views.login_view, name='login'),
    
    # Outras URLs
        path('logout/', views.logout_view, name='logout'),
        path('documentos/', include([
        path('', views.lista_documentos, name='lista_documentos'),
        path('upload/', views.upload_documento, name='upload_documento'),
        path('<int:documento_id>/download/', views.download_documento, name='download_documento'),
        path('<int:documento_id>/permissoes/', views.gerenciar_permissoes, name='gerenciar_permissoes'),
        path('<int:documento_id>/assinar/', views.assinar_documento, name='assinar_documento'),
    ])),
]

# Configuração para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)