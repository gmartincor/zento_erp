from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal
from datetime import date


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('legal_form', models.CharField(choices=[('AUTONOMO', 'Autónomo/a'), ('SL', 'Sociedad Limitada (SL)'), ('SA', 'Sociedad Anónima (SA)'), ('SLU', 'Sociedad Limitada Unipersonal (SLU)'), ('SCP', 'Sociedad Civil Privada (SCP)'), ('CB', 'Comunidad de Bienes (CB)')], max_length=20, verbose_name='Forma jurídica')),
                ('business_name', models.CharField(max_length=200, verbose_name='Nombre comercial')),
                ('legal_name', models.CharField(blank=True, max_length=200, verbose_name='Razón social')),
                ('tax_id', models.CharField(max_length=15, verbose_name='NIF/CIF')),
                ('address', models.TextField(verbose_name='Dirección')),
                ('postal_code', models.CharField(max_length=10, verbose_name='Código postal')),
                ('city', models.CharField(max_length=100, verbose_name='Ciudad')),
                ('province', models.CharField(blank=True, max_length=100, verbose_name='Provincia')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('bank_name', models.CharField(max_length=100, verbose_name='Banco')),
                ('iban', models.CharField(max_length=34, verbose_name='IBAN')),
                ('mercantile_registry', models.CharField(blank=True, max_length=200, verbose_name='Registro Mercantil')),
                ('share_capital', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Capital social')),
                ('invoice_prefix', models.CharField(default='FN', max_length=10, verbose_name='Prefijo de factura')),
                ('current_number', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('logo', models.ImageField(blank=True, null=True, upload_to='company/logos/')),
            ],
            options={
                'verbose_name_plural': 'Companies',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('reference', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('issue_date', models.DateField(default=date.today, verbose_name='Fecha de emisión')),
                ('client_type', models.CharField(choices=[('COMPANY', 'Empresa'), ('FREELANCER', 'Autónomo'), ('INDIVIDUAL', 'Particular')], max_length=20, verbose_name='Tipo de cliente')),
                ('client_name', models.CharField(max_length=200, verbose_name='Nombre del cliente')),
                ('client_tax_id', models.CharField(blank=True, max_length=15, verbose_name='NIF/CIF del cliente')),
                ('client_address', models.TextField(verbose_name='Dirección del cliente')),
                ('status', models.CharField(choices=[('DRAFT', 'Borrador'), ('SENT', 'Enviada'), ('PAID', 'Pagada')], default='DRAFT', max_length=20, verbose_name='Estado')),
                ('payment_terms', models.TextField(default='Transferencia bancaria', verbose_name='Condiciones de pago')),
                ('pdf_file', models.FileField(blank=True, upload_to='invoices/pdfs/')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoicing.company')),
            ],
            options={
                'ordering': ['-issue_date'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Descripción')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Cantidad')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio unitario')),
                ('vat_rate', models.DecimalField(decimal_places=2, default=21.00, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='IVA (%)')),
                ('irpf_rate', models.DecimalField(decimal_places=2, default=0.00, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='IRPF (%)')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='invoicing.invoice')),
            ],
        ),
    ]
