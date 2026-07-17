from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import SenalTrading, PerfilSuscripcion

# 1. VISTA DEL PANEL (Protegida)
@login_required(login_url='/login/')
def inicio_panel(request):
    perfil, created = PerfilSuscripcion.objects.get_or_create(usuario=request.user)
    
    if not perfil.verificar_acceso():
        return redirect('pago_qr')
        
    senales = SenalTrading.objects.all().order_by('-fecha_creacion')[:10]
    return render(request, 'panel.html', {'senales': senales})

# 2. VISTA DE LA PÁGINA DE PAGO (Protegida)
@login_required(login_url='/login/')
def pagina_pago(request):
    perfil = PerfilSuscripcion.objects.get(usuario=request.user)
    return render(request, 'pago.html', {'perfil': perfil})

# 3. VISTA DE INICIO DE SESIÓN
def vista_login(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('username')
        contra = request.POST.get('password')
        
        user = authenticate(request, username=usuario, password=contra)
        
        if user is not None:
            login(request, user)
            return redirect('inicio_panel')
        else:
            error = 'Usuario o contraseña incorrectos. Intentá de nuevo.'
            
    return render(request, 'login.html', {'error': error})

# 4. VISTA DE REGISTRO PARA TIKTOK
def vista_registro(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('username')
        contra = request.POST.get('password')
        
        try:
            user = User.objects.create_user(username=usuario, password=contra)
            PerfilSuscripcion.objects.create(usuario=user)
            login(request, user)
            return redirect('inicio_panel')
            
        except IntegrityError:
            error = 'Ese nombre de usuario ya está en uso. Elegí otro.'
            
    return render(request, 'registro.html', {'error': error})

    from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Apagamos el guardia de seguridad SOLO para esta puerta, para que el bot pueda entrar
def recibir_senal(request):
    if request.method == 'POST':
        simbolo = request.POST.get('simbolo', '')
        tipo = request.POST.get('tipo', '')
        precio = request.POST.get('precio', '')
        sl = request.POST.get('sl', '')
        tp = request.POST.get('tp', '')
        
        # Por ahora solo imprimimos en la consola de Render para verificar que llega
        print(f"🔥 SEÑAL RECIBIDA DEL BOT: {tipo} en {simbolo} | Entrada: {precio} | SL: {sl} | TP: {tp}")
        
        return JsonResponse({'status': 'ok', 'mensaje': 'Señal recibida en la bóveda VIP'})
    
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=400)