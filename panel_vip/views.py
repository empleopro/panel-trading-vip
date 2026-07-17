from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SenalTrading, PerfilSuscripcion

# Importes necesarios para Pagopar
import json
from django.utils import timezone
from datetime import timedelta

# 1. VISTA DEL PANEL (Protegida)
@login_required(login_url='/login/')
def inicio_panel(request):
    perfil, created = PerfilSuscripcion.objects.get_or_create(usuario=request.user)
    
    if not perfil.verificar_acceso():
        return redirect('pagina_pago')
        
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

# 5. WEBHOOK PARA RECIBIR SEÑALES DEL BOT
@csrf_exempt
def recibir_senal(request):
    if request.method == 'POST':
        try:
            # Captura de datos que envía el bot
            simbolo = request.POST.get('simbolo', 'XAUUSD')
            tipo = request.POST.get('tipo', 'BUY')
            precio = request.POST.get('precio', 0)
            sl = request.POST.get('sl', 0)
            tp = request.POST.get('tp', 0)
            
            # Guardado en base de datos usando los nombres exactos de tu models.py
            SenalTrading.objects.create(
                activo=simbolo,         
                tipo=tipo,              
                precio_entrada=precio,  
                sl=sl,                  
                tp=tp                   
            )
            
            print(f"🔥 SEÑAL RECIBIDA Y GUARDADA: {tipo} en {simbolo}")
            return JsonResponse({'status': 'ok', 'mensaje': 'Señal guardada correctamente'})
            
        except Exception as e:
            print(f"ERROR CRÍTICO AL GUARDAR SEÑAL: {str(e)}")
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=400)


# 6. WEBHOOK PARA RECIBIR PAGOS DE PAGOPAR (AUTOMATIZACIÓN)
@csrf_exempt
def notificacion_pagopar(request):
    if request.method == 'POST':
        try:
            # Pagopar avisa acá cuando alguien paga
            data = json.loads(request.body)
            estado = data.get('estado') 
            id_pedido = data.get('id_pedido') # Acá vendrá el nombre de usuario de tu cliente
            
            if estado == 'pagado':
                # Buscamos al usuario y le damos 30 días de acceso VIP
                usuario = User.objects.get(username=id_pedido)
                perfil = PerfilSuscripcion.objects.get(usuario=usuario)
                perfil.estado = 'ACTIVO'
                perfil.fecha_fin_acceso = timezone.now() + timedelta(days=30)
                perfil.save()
                
                print(f"✅ PAGO APROBADO: Acceso VIP activado para {id_pedido}")
                return JsonResponse({'status': 'ok'})
            
            return JsonResponse({'status': 'pendiente'})
            
        except Exception as e:
            print(f"❌ ERROR EN PAGOPAR: {str(e)}")
            return JsonResponse({'status': 'error'}, status=500)
    
    return JsonResponse({'status': 'error'}, status=400)