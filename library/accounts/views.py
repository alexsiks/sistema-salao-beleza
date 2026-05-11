import requests as http_requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, UserProfileForm
from .models import ActionLog, UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('books:list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            ActionLog.log(user=user, action='LOGIN',
                          description=f'Login bem-sucedido: {user.username}', request=request)
            return redirect(request.GET.get('next', 'books:list'))
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        ActionLog.log(user=request.user, action='LOGOUT',
                      description=f'Logout: {request.user.username}', request=request)
    logout(request)
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('books:list')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        ActionLog.log(user=user, action='REGISTER',
                      description=f'Novo usuário registrado: {user.username} ({user.email})',
                      request=request,
                      extra_data={'username': user.username, 'email': user.email,
                                  'first_name': user.first_name, 'last_name': user.last_name})
        login(request, user)
        messages.success(request, 'Conta criada com sucesso! Bem-vindo(a)!')
        return redirect('books:list')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            form.save()
            ActionLog.log(user=request.user, action='PROFILE_UPDATE',
                          description=f'Perfil atualizado: {request.user.username}',
                          request=request)
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def lookup_cep(request):
    cep = request.GET.get('cep', '').replace('-', '').replace('.', '').strip()
    if len(cep) != 8:
        from django.http import JsonResponse
        return JsonResponse({'error': 'CEP inválido'}, status=400)
    try:
        resp = http_requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
        data = resp.json()
        if 'erro' in data:
            from django.http import JsonResponse
            return JsonResponse({'error': 'CEP não encontrado'}, status=404)
        from django.http import JsonResponse
        return JsonResponse({
            'logradouro': data.get('logradouro', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'estado': data.get('uf', ''),
            'complemento': data.get('complemento', ''),
        })
    except Exception:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Erro ao consultar CEP'}, status=500)


@login_required
def user_list_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    users = User.objects.select_related('profile').order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def action_log_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    logs = ActionLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'accounts/action_logs.html', {'logs': logs})
