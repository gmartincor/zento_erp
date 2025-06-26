from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_migrate_status_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientservice',
            name='status',
        ),
    ]
