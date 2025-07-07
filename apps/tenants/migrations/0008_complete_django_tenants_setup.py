# Generated manually for django-tenants final migration

from django.db import migrations, models
import django.db.models.deletion
import django_tenants.postgresql_backend.base


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0007_populate_schema_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(db_index=True, max_length=253, unique=True)),
                ('is_primary', models.BooleanField(db_index=True, default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='tenant',
            name='schema_name',
            field=models.CharField(db_index=True, max_length=63, unique=True, validators=[django_tenants.postgresql_backend.base._check_schema_name]),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='slug',
            field=models.CharField(db_index=True, help_text='Identificador único para URLs (ej: maria-fernandez -> /maria-fernandez/)', max_length=63, unique=True, verbose_name='Slug'),
        ),
        migrations.AddIndex(
            model_name='tenant',
            index=models.Index(fields=['slug'], name='tenants_ten_slug_63daca_idx'),
        ),
        migrations.AddField(
            model_name='domain',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='tenants.tenant'),
        ),
    ]
