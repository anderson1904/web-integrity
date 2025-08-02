from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import hashlib
import datetime
from .models import Usuario, Documento, PermissaoDocumento, Assinatura, LogDocumento, Caligrafia
from .forms import DocumentoForm, PermissaoForm, LoginForm

# Autenticação
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            
            try:
                usuario = Usuario.objects.get(email_usuario=email)
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                
                if usuario.senha_hash == senha_hash:
                    # Aqui você precisaria implementar seu próprio sistema de login
                    # já que não está usando o sistema de autenticação padrão do Django
                    request.session['usuario_id'] = usuario.id
                    return redirect('lista_documentos')
                else:
                    return render(request, 'login.html', {
                        'form': form,
                        'erro': 'Credenciais inválidas'
                    })
            except Usuario.DoesNotExist:
                return render(request, 'login.html', {
                    'form': form,
                    'erro': 'Usuário não encontrado'
                })
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if 'usuario_id' in request.session:
        del request.session['usuario_id']
    return redirect('login')

# Documentos
@login_required
def upload_documento(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.usuario_dono = request.user
            
            # Calcula hash do arquivo
            arquivo = request.FILES['caminho_arquivo']
            hash_arquivo = hashlib.sha256()
            for chunk in arquivo.chunks():
                hash_arquivo.update(chunk)
            
            documento.hash_arquivo = hash_arquivo.hexdigest()
            documento.save()
            
            # Cria permissão para o dono
            PermissaoDocumento.objects.create(
                documento=documento,
                usuario=request.user,
                pode_visualizar=True,
                pode_assinar=True
            )
            
            # Log da ação
            LogDocumento.objects.create(
                documento=documento,
                usuario=request.user,
                acao='Upload do documento',
                ip_origem=get_client_ip(request)
            )
            
            return redirect('lista_documentos')
    else:
        form = DocumentoForm()
    
    return render(request, 'upload_documento.html', {'form': form})

@login_required
def lista_documentos(request):
    documentos = Documento.objects.filter(
        Q(usuario_dono=request.user) |
        Q(permissoes__usuario=request.user, permissoes__pode_visualizar=True)
    ).distinct()
    
    return render(request, 'lista_documentos.html', {'documentos': documentos})

@login_required
def download_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    
    # Verifica permissão
    if documento.usuario_dono != request.user and not PermissaoDocumento.objects.filter(
        documento=documento,
        usuario=request.user,
        pode_visualizar=True
    ).exists():
        raise PermissionDenied("Você não tem permissão para acessar este documento")
    
    # Log da ação
    LogDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='Download do documento',
        ip_origem=get_client_ip(request)
    )
    
    response = FileResponse(documento.caminho_arquivo)
    response['Content-Disposition'] = f'attachment; filename="{documento.caminho_arquivo.name}"'
    return response

# Permissões
@login_required
def gerenciar_permissoes(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    
    # Verifica se o usuário é o dono do documento
    if documento.usuario_dono != request.user:
        raise PermissionDenied("Apenas o dono do documento pode gerenciar permissões")
    
    if request.method == 'POST':
        form = PermissaoForm(request.POST)
        if form.is_valid():
            permissao = form.save(commit=False)
            permissao.documento = documento
            permissao.save()
            
            # Log da ação
            LogDocumento.objects.create(
                documento=documento,
                usuario=request.user,
                acao=f'Permissões atualizadas para {permissao.usuario.nome_usuario}',
                ip_origem=get_client_ip(request)
            )
            
            return redirect('gerenciar_permissoes', documento_id=documento.id)
    else:
        form = PermissaoForm()
    
    permissoes = PermissaoDocumento.objects.filter(documento=documento)
    return render(request, 'gerenciar_permissoes.html', {
        'form': form,
        'documento': documento,
        'permissoes': permissoes
    })

# Assinaturas
@login_required
def assinar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    
    # Verifica se o usuário tem permissão para assinar
    if not PermissaoDocumento.objects.filter(
        documento=documento,
        usuario=request.user,
        pode_assinar=True
    ).exists():
        raise PermissionDenied("Você não tem permissão para assinar este documento")
    
    # Verifica se já assinou
    if Assinatura.objects.filter(documento=documento, usuario=request.user).exists():
        return render(request, 'erro.html', {
            'erro': 'Você já assinou este documento'
        }, status=400)
    
    if request.method == 'POST':
        # Gera hash da assinatura
        assinatura_hash = hashlib.sha256(
            f"{documento.id}{request.user.id}{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Cria a assinatura
        Assinatura.objects.create(
            documento=documento,
            usuario=request.user,
            assinatura_hash=assinatura_hash
        )
        
        # Atualiza status do documento se todas as assinaturas necessárias foram feitas
        atualizar_status_documento(documento)
        
        # Log da ação
        LogDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            acao='Assinatura digital realizada',
            ip_origem=get_client_ip(request)
        )
        
        return redirect('lista_documentos')
    
    return render(request, 'assinar_documento.html', {'documento': documento})

def atualizar_status_documento(documento):
    usuarios_com_permissao = PermissaoDocumento.objects.filter(
        documento=documento,
        pode_assinar=True
    ).values_list('usuario', flat=True)
    
    assinaturas = Assinatura.objects.filter(documento=documento).values_list('usuario', flat=True)
    
    if set(usuarios_com_permissao).issubset(set(assinaturas)):
        documento.status = 'finalizado'
        documento.save()

# Função auxiliar para pegar IP do cliente
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip