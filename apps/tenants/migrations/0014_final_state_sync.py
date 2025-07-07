# Final state synchronization migration

from django.db import migrations, models
from django.db import connection


def check_and_sync_constraints(apps, schema_editor):
    """Ensure the database state matches what Django expects"""
    with connection.cursor() as cursor:
        # Check if tenant_subdomain_format constraint exists
        cursor.execute("""
            SELECT COUNT(*) FROM pg_constraint 
            WHERE conname = 'tenant_subdomain_format' 
            AND conrelid = 'tenants_tenant'::regclass
        """)
        subdomain_constraint_exists = cursor.fetchone()[0] > 0
        
        # Check if tenants_ten_subdoma_6c6a7a_idx index exists
        cursor.execute("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE indexname = 'tenants_ten_subdoma_6c6a7a_idx' 
            AND tablename = 'tenants_tenant'
        """)
        subdomain_index_exists = cursor.fetchone()[0] > 0
        
        # Check if tenant_slug_format constraint exists
        cursor.execute("""
            SELECT COUNT(*) FROM pg_constraint 
            WHERE conname = 'tenant_slug_format' 
            AND conrelid = 'tenants_tenant'::regclass
        """)
        slug_constraint_exists = cursor.fetchone()[0] > 0
        
        # Remove old constraints/indices if they exist
        if subdomain_constraint_exists:
            cursor.execute("ALTER TABLE tenants_tenant DROP CONSTRAINT tenant_subdomain_format")
            
        if subdomain_index_exists:
            cursor.execute("DROP INDEX tenants_ten_subdoma_6c6a7a_idx")
            
        # Ensure slug constraint exists
        if not slug_constraint_exists:
            cursor.execute("""
                ALTER TABLE tenants_tenant ADD CONSTRAINT tenant_slug_format 
                CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$')
            """)


def reverse_sync(apps, schema_editor):
    """No reverse operation needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0013_remove_tenant_tenant_subdomain_format_and_more'),
    ]

    operations = [
        migrations.RunPython(check_and_sync_constraints, reverse_sync),
    ]
