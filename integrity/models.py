from django.db import models
from django.contrib.auth.models import AbstractUser

# Se quiser personalizar usuário, pode estender AbstractUser.
# Aqui vou manter um modelo simples:

class Usuario(models.Model):
    FUNCOES = [
        ('usuario', 'Usuário'),
        ('admin', 'Administrador'),
        ('validador', 'Validador'),
    ]

    nome_usuario = models.CharField(max_length=100)
    email_usuario = models.EmailField(unique=True)
    senha_hash = models.CharField(max_length=255)
    funcao = models.CharField(max_length=10, choices=FUNCOES, default='usuario')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_usuario


class Documento(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('em_assinatura', 'Em Assinatura'),
        ('finalizado', 'Finalizado'),
        ('suspeito', 'Suspeito'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    caminho_arquivo = models.CharField(max_length=255)
    hash_arquivo = models.CharField(max_length=128)
    usuario_dono = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='documentos_enviados')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enviado')
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Caligrafia(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='caligrafias')
    imagem_assinatura = models.CharField(max_length=255)
    resultado_ocr = models.TextField(blank=True)
    confianca = models.FloatField()
    suspeita_falsificacao = models.BooleanField(default=False)
    data_analise = models.DateTimeField(auto_now_add=True)


class Assinatura(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='assinaturas')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='assinaturas')
    assinatura_hash = models.CharField(max_length=255)
    carimbo_tempo = models.DateTimeField(auto_now_add=True)


class PermissaoDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='permissoes')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='permissoes')
    pode_visualizar = models.BooleanField(default=False)
    pode_assinar = models.BooleanField(default=False)

    def __str__(self):
        return f'Permissão de {self.usuario} para {self.documento}'


class LogDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='logs')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='logs')
    acao = models.CharField(max_length=100)
    ip_origem = models.CharField(max_length=45)
    data_log = models.DateTimeField(auto_now_add=True)
