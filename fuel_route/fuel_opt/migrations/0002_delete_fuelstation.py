from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fuel_opt", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="FuelStation"),
    ]
