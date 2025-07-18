from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoicing', '0002_fix_reference_null'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE invoicing_invoice ALTER COLUMN reference DROP NOT NULL;",
            reverse_sql="ALTER TABLE invoicing_invoice ALTER COLUMN reference SET NOT NULL;",
        ),
    ]
