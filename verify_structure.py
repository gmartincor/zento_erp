#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/guillermomartincorrea/Desktop/Repositorios_personales/nutrition-pro/crm-nutricion-pro')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# Setup Django
django.setup()

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService

print('=== ESTRUCTURA JERÁRQUICA ACTUAL ===')
for bl in BusinessLine.objects.filter(level=1).order_by('order'):
    print(f'Nivel 1: {bl.name} (ID: {bl.id})')
    for child in bl.children.all().order_by('order'):
        print(f'  └── Nivel 2: {child.name} (ID: {child.id})')
        if child.has_remanente:
            print(f'      └── has_remanente=True, remanente_field={child.remanente_field}')
        for grandchild in child.children.all().order_by('order'):
            print(f'      └── Nivel 3: {grandchild.name} (ID: {grandchild.id})')
            if grandchild.has_remanente:
                print(f'          └── has_remanente=True, remanente_field={grandchild.remanente_field}')

print('\n=== RESUMEN DE ESTRUCTURA ===')
print(f'Total business lines: {BusinessLine.objects.count()}')
print(f'Nivel 1: {BusinessLine.objects.filter(level=1).count()}')
print(f'Nivel 2: {BusinessLine.objects.filter(level=2).count()}')
print(f'Nivel 3: {BusinessLine.objects.filter(level=3).count()}')

print('\n=== TABLA DE REMANENTES POR LÍNEA ===')
print('ID\tLínea de Negocio\t\tCategoría White\tCategoría Black\t\tCampo Remanente')
print('-' * 100)
for bl in BusinessLine.objects.all().order_by('id'):
    white_services = ClientService.objects.filter(business_line=bl, category='WHITE').count()
    black_services = ClientService.objects.filter(business_line=bl, category='BLACK').count()
    
    white_status = f'{white_services} servicios' if white_services > 0 else 'Sin servicios'
    
    if bl.has_remanente and black_services > 0:
        black_status = f'{black_services} con remanente'
    elif black_services > 0:
        black_status = f'{black_services} sin remanente'
    else:
        black_status = 'Sin servicios'
    
    remanente_field = bl.remanente_field if bl.has_remanente else '-'
    
    name_padded = bl.name.ljust(20)
    white_padded = white_status.ljust(12)
    black_padded = black_status.ljust(15)
    
    print(f'{bl.id}\t{name_padded}\t{white_padded}\t{black_padded}\t{remanente_field}')

print('\n=== VERIFICACIÓN DE ESTRUCTURA SOLICITADA ===')
expected_structure = {
    'Jaen': {'level': 1, 'children': ['NPV', 'PEPE']},
    'NPV': {'level': 2, 'parent': 'Jaen'},
    'PEPE': {'level': 2, 'parent': 'Jaen', 'children': ['PEPE-normal', 'PEPE-videoCall']},
    'PEPE-normal': {'level': 3, 'parent': 'PEPE', 'remanente': 'remanente_pepe'},
    'PEPE-videoCall': {'level': 3, 'parent': 'PEPE', 'remanente': 'remanente_pepe_video'},
    'Glow': {'level': 1, 'children': ['Dani-Rubi', 'Dani', 'Rubi Glow']},
    'Dani-Rubi': {'level': 2, 'parent': 'Glow', 'remanente': 'remanente_dani'},
    'Dani': {'level': 2, 'parent': 'Glow', 'remanente': 'remanente_aven'},
    'Rubi Glow': {'level': 2, 'parent': 'Glow'},
    'Rubi': {'level': 1, 'children': ['Presencial', 'Online']},
    'Presencial': {'level': 2, 'parent': 'Rubi'},
    'Online': {'level': 2, 'parent': 'Rubi'}
}

print('Verificando estructura solicitada:')
all_correct = True

for name, expected in expected_structure.items():
    try:
        if name == 'Rubi' and expected['level'] == 1:
            # Este es el Rubi independiente
            bl = BusinessLine.objects.get(name=name, level=1)
        elif name == 'Rubi' and 'parent' in expected:
            # Este es el Rubi hijo de Glow
            glow = BusinessLine.objects.get(name='Glow')
            bl = BusinessLine.objects.get(name=name, parent=glow)
        else:
            bl = BusinessLine.objects.get(name=name)
        
        # Verificar nivel
        if bl.level != expected['level']:
            print(f'❌ {name}: nivel incorrecto (esperado: {expected["level"]}, actual: {bl.level})')
            all_correct = False
        
        # Verificar padre
        if 'parent' in expected:
            parent_name = expected['parent']
            expected_parent = BusinessLine.objects.get(name=parent_name)
            if bl.parent != expected_parent:
                print(f'❌ {name}: padre incorrecto (esperado: {parent_name}, actual: {bl.parent})')
                all_correct = False
        
        # Verificar remanente
        if 'remanente' in expected:
            if not bl.has_remanente or bl.remanente_field != expected['remanente']:
                print(f'❌ {name}: remanente incorrecto (esperado: {expected["remanente"]}, actual: {bl.remanente_field})')
                all_correct = False
        
        if all_correct:
            status = '✅'
        else:
            status = '❌'
        print(f'{status} {name}: OK')
        
    except BusinessLine.DoesNotExist:
        print(f'❌ {name}: NO ENCONTRADO')
        all_correct = False

if all_correct:
    print('\n🎉 ¡ESTRUCTURA COMPLETAMENTE CORRECTA!')
else:
    print('\n⚠️  Hay problemas en la estructura')
