# Generated manually to complete tenant model constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0009_fix_slug_constraints'),
    ]

    operations = [
        # Ensure the slug constraint exists with the correct name
        # This should be idempotent - if it exists, it won't fail
        migrations.RunSQL(
            sql="DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tenant_slug_format') THEN ALTER TABLE tenants_tenant ADD CONSTRAINT tenant_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$'); END IF; END $$;",
            reverse_sql="ALTER TABLE tenants_tenant DROP CONSTRAINT IF EXISTS tenant_slug_format;"
        ),
    ]
