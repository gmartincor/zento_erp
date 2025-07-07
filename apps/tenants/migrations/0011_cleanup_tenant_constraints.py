# Generated manually to clean up tenant constraints properly

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0010_ensure_slug_constraint'),
    ]

    operations = [
        # Remove any old subdomain constraint if it exists (safe removal)
        migrations.RunSQL(
            sql="ALTER TABLE tenants_tenant DROP CONSTRAINT IF EXISTS tenant_subdomain_format;",
            reverse_sql="-- No reverse operation needed"
        ),
        # Remove any old subdomain index if it exists (safe removal)  
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS tenants_ten_subdoma_6c6a7a_idx;",
            reverse_sql="-- No reverse operation needed"
        ),
        # Ensure the correct slug constraint exists
        migrations.RunSQL(
            sql="DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tenant_slug_format') THEN ALTER TABLE tenants_tenant ADD CONSTRAINT tenant_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$'); END IF; END $$;",
            reverse_sql="ALTER TABLE tenants_tenant DROP CONSTRAINT IF EXISTS tenant_slug_format;"
        ),
    ]
