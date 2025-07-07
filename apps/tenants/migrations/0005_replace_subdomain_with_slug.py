# Generated migration to properly handle slug field addition

from django.db import migrations, models
import django.db.models.deletion


def populate_slug_from_subdomain(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    for i, tenant in enumerate(Tenant.objects.all()):
        if hasattr(tenant, 'subdomain') and tenant.subdomain:
            tenant.slug = tenant.subdomain
        else:
            tenant.slug = f'tenant-{tenant.id or i+1}'
        tenant.save()


def reverse_populate_slug(apps, schema_editor):
    # Reverse migration - not really needed for this case
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_remove_tenant_schema_name_delete_domain'),
    ]

    operations = [
        # Remove old constraints and indexes
        migrations.RunSQL(
            "ALTER TABLE tenants_tenant DROP CONSTRAINT IF EXISTS tenant_subdomain_format;",
            reverse_sql="-- No reverse needed"
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS tenants_ten_subdoma_6c6a7a_idx;",
            reverse_sql="-- No reverse needed"
        ),
        
        # Add slug field (nullable first)
        migrations.AddField(
            model_name='tenant',
            name='slug',
            field=models.CharField(
                max_length=63, 
                null=True, 
                blank=True,
                verbose_name="Slug",
                help_text="Identificador único para URLs"
            ),
        ),
        
        # Populate slug values
        migrations.RunPython(populate_slug_from_subdomain, reverse_populate_slug),
        
        # Make slug unique and required
        migrations.AlterField(
            model_name='tenant',
            name='slug',
            field=models.CharField(
                max_length=63,
                unique=True,
                verbose_name="Slug",
                help_text="Identificador único para URLs (ej: maria-fernandez -> /maria-fernandez/)",
                db_index=True
            ),
        ),
        
        # Remove subdomain field
        migrations.RemoveField(
            model_name='tenant',
            name='subdomain',
        ),
        
        # Add new constraint
        migrations.RunSQL(
            "ALTER TABLE tenants_tenant ADD CONSTRAINT tenant_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$');",
            reverse_sql="ALTER TABLE tenants_tenant DROP CONSTRAINT IF EXISTS tenant_slug_format;"
        ),
    ]
