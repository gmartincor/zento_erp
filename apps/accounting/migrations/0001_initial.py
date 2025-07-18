from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('business_lines', '0001_unified_business_lines'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Eliminado')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación')),
                ('full_name', models.CharField(max_length=255, verbose_name='Nombre completo')),
                ('dni', models.CharField(help_text='Documento de identidad único', max_length=20, unique=True, verbose_name='DNI/NIE')),
                ('gender', models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], max_length=1, verbose_name='Género')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Correo electrónico')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('notes', models.TextField(blank=True, help_text='Información adicional sobre el cliente', verbose_name='Notas')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'clients',
            },
        ),
        migrations.CreateModel(
            name='ClientService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('category', models.CharField(choices=[('personal', 'Personal'), ('business', 'Business')], max_length=10, verbose_name='Categoría')),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Precio base')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Fecha de inicio')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Fecha de finalización')),
                ('admin_status', models.CharField(choices=[('ENABLED', 'Habilitado'), ('SUSPENDED', 'Suspendido temporalmente')], default='ENABLED', help_text='Control administrativo independiente del estado operacional', max_length=15, verbose_name='Estado administrativo')),
                ('notes', models.TextField(blank=True, help_text='Observaciones específicas del servicio', verbose_name='Notas del servicio')),
                ('remanentes', models.JSONField(blank=True, default=dict, help_text='Información de remanentes para categoría BUSINESS', verbose_name='Remanentes')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Activo')),
                ('business_line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_services', to='business_lines.businessline', verbose_name='Línea de negocio')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='accounting.client', verbose_name='Cliente')),
            ],
            options={
                'verbose_name': 'Servicio de cliente',
                'verbose_name_plural': 'Servicios de clientes',
                'db_table': 'client_services',
            },
        ),
        migrations.CreateModel(
            name='ServicePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, help_text='Monto del pago (opcional para períodos sin pago)', max_digits=10, null=True, verbose_name='Monto')),
                ('payment_date', models.DateField(blank=True, help_text='Fecha de pago (opcional para períodos sin pago)', null=True, verbose_name='Fecha de pago')),
                ('period_start', models.DateField(verbose_name='Inicio del período')),
                ('period_end', models.DateField(verbose_name='Fin del período')),
                ('status', models.CharField(choices=[('AWAITING_START', 'Periodo creado sin pago'), ('UNPAID_ACTIVE', 'Pendiente de pago'), ('PAID', 'Pagado'), ('OVERDUE', 'Vencido'), ('REFUNDED', 'Reembolsado')], default='AWAITING_START', max_length=15, verbose_name='Estado')),
                ('payment_method', models.CharField(blank=True, choices=[('CARD', 'Tarjeta'), ('CASH', 'Efectivo'), ('TRANSFER', 'Transferencia'), ('BIZUM', 'Bizum'), ('PAYPAL', 'PayPal'), ('OTHER', 'Otro')], help_text='Método de pago (opcional para períodos sin pago)', max_length=15, null=True, verbose_name='Método de pago')),
                ('reference_number', models.CharField(blank=True, help_text='Referencia de la transacción', max_length=100, verbose_name='Número de referencia')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('remanente', models.DecimalField(blank=True, decimal_places=2, help_text='Cantidad de remanente aplicado (positivo o negativo)', max_digits=10, null=True, verbose_name='Remanente')),
                ('refunded_amount', models.DecimalField(decimal_places=2, default=0, help_text='Cantidad reembolsada del pago original', max_digits=10, verbose_name='Monto reembolsado')),
                ('client_service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounting.clientservice', verbose_name='Servicio')),
            ],
            options={
                'verbose_name': 'Pago de servicio',
                'verbose_name_plural': 'Pagos de servicios',
                'db_table': 'service_payments',
                'ordering': ['-payment_date', '-created'],
            },
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['dni'], name='clients_dni_fc9f79_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['is_active', 'full_name'], name='clients_is_acti_e5cf1e_idx'),
        ),
        migrations.AddIndex(
            model_name='clientservice',
            index=models.Index(fields=['client', 'is_active'], name='client_serv_client__815139_idx'),
        ),
        migrations.AddIndex(
            model_name='clientservice',
            index=models.Index(fields=['business_line', 'category'], name='client_serv_busines_d6c053_idx'),
        ),
        migrations.AddIndex(
            model_name='clientservice',
            index=models.Index(fields=['client', 'business_line', 'category', 'created'], name='client_serv_client__2561e8_idx'),
        ),
        migrations.AddIndex(
            model_name='servicepayment',
            index=models.Index(fields=['client_service', 'status'], name='service_pay_client__cdcd9d_idx'),
        ),
        migrations.AddIndex(
            model_name='servicepayment',
            index=models.Index(fields=['payment_date'], name='service_pay_payment_3ffc00_idx'),
        ),
        migrations.AddIndex(
            model_name='servicepayment',
            index=models.Index(fields=['period_start', 'period_end'], name='service_pay_period__fe7dc9_idx'),
        ),
        migrations.AddIndex(
            model_name='servicepayment',
            index=models.Index(fields=['status', 'payment_date'], name='service_pay_status_647630_idx'),
        ),
    ]
