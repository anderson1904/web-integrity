# integrity/forms.py
from django import forms
from .models import Documento, PermissaoDocumento, Usuario

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['titulo', 'descricao', 'caminho_arquivo']

class PermissaoForm(forms.ModelForm):
    class Meta:
        model = PermissaoDocumento
        fields = ['usuario', 'pode_visualizar', 'pode_assinar']

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)