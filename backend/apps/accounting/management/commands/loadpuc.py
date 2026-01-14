"""
Management command to load PUC (Plan Único de Cuentas) from desktop/src/puc-data.json
"""
import json
import os
from django.core.management.base import BaseCommand
from apps.accounting.models import AccountClass, AccountGroup, Account


class Command(BaseCommand):
    help = 'Carga el Plan Único de Cuentas (PUC) desde puc-data.json'

    def handle(self, *args, **options):
        # Ruta al archivo puc-data.json
        puc_file = os.path.join(
            os.path.dirname(__file__),
            '../../../../../desktop/src/puc-data.json'
        )
        
        if not os.path.exists(puc_file):
            self.stdout.write(self.style.ERROR(f'❌ Archivo no encontrado: {puc_file}'))
            return
        
        with open(puc_file, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
        
        self.stdout.write(f'📄 Cargando {len(accounts_data)} cuentas del PUC...')
        
        # Primero crear las clases de cuenta (nivel 1)
        classes_created = 0
        groups_created = 0
        accounts_created = 0
        errors = 0
        
        # Diccionario para almacenar los IDs de las cuentas padre
        accounts_map = {}
        
        # Ordenar por código para asegurar que las cuentas padre se creen primero
        accounts_data_sorted = sorted(accounts_data, key=lambda x: x['code'])
        
        for acc_data in accounts_data_sorted:
            try:
                code = acc_data['code']
                name = acc_data['name']
                level = acc_data['level']
                nature = acc_data['nature']
                account_type = acc_data['account_type']
                allows_movement = acc_data.get('allows_movement', True)
                
                # Nivel 1: Clases de cuenta
                if level == 1:
                    account_class, created = AccountClass.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'nature': nature,
                            'is_active': True
                        }
                    )
                    if created:
                        classes_created += 1
                    accounts_map[code] = account_class
                
                # Nivel 2: Grupos de cuenta
                elif level == 2:
                    class_code = code[0]
                    account_class = accounts_map.get(class_code)
                    
                    if not account_class:
                        account_class = AccountClass.objects.filter(code=class_code).first()
                        if account_class:
                            accounts_map[class_code] = account_class
                    
                    if account_class:
                        account_group, created = AccountGroup.objects.get_or_create(
                            code=code,
                            defaults={
                                'account_class': account_class,
                                'name': name,
                                'is_active': True
                            }
                        )
                        if created:
                            groups_created += 1
                        accounts_map[code] = account_group
                
                # Nivel 3+: Cuentas
                else:
                    # Obtener el grupo (primeros 2 dígitos)
                    group_code = code[:2]
                    account_group = accounts_map.get(group_code)
                    
                    if not account_group:
                        account_group = AccountGroup.objects.filter(code=group_code).first()
                        if account_group:
                            accounts_map[group_code] = account_group
                    
                    if not account_group:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️  Grupo {group_code} no encontrado para cuenta {code}'
                        ))
                        errors += 1
                        continue
                    
                    # Determinar la cuenta padre
                    parent = None
                    if level > 3:
                        # Buscar la cuenta padre (código con un dígito menos)
                        parent_code = code[:-2] if len(code) > 4 else code[:4]
                        parent = accounts_map.get(parent_code)
                        
                        if not parent:
                            parent = Account.objects.filter(code=parent_code).first()
                            if parent:
                                accounts_map[parent_code] = parent
                    
                    account, created = Account.objects.get_or_create(
                        code=code,
                        defaults={
                            'account_group': account_group,
                            'name': name,
                            'level': level,
                            'parent': parent,
                            'nature': nature,
                            'account_type': account_type,
                            'allows_movement': allows_movement,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        accounts_created += 1
                    accounts_map[code] = account
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error en cuenta {acc_data.get("code", "?")} : {str(e)}'))
                errors += 1
        
        self.stdout.write(self.style.SUCCESS('\n✅ Carga del PUC completada:'))
        self.stdout.write(f'   • Clases creadas: {classes_created}')
        self.stdout.write(f'   • Grupos creados: {groups_created}')
        self.stdout.write(f'   • Cuentas creadas: {accounts_created}')
        if errors > 0:
            self.stdout.write(self.style.WARNING(f'   • Errores: {errors}'))
