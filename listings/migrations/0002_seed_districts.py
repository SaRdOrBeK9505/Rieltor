from django.db import migrations


def seed_districts(apps, schema_editor):
    District = apps.get_model('listings', 'District')
    
    # 12 ta tuman (Bektemirsiz) - owner bilan tasdiqlangan ro'yxat
    DISTRICTS = [
        "Chilonzor",
        "Yunusobod",
        "Mirzo Ulug'bek",
        "Shayxontohur",
        "Yashnobod",
        "Uchtepa",
        "Yakkasaroy",
        "Sergeli",
        "Olmazor",
        "Mirobod",
        "Yangihayot",
        "Qo'qon",  # Placeholder - owner bilan aniqlashtirish kerak
    ]
    
    for district_name in DISTRICTS:
        District.objects.get_or_create(name=district_name)


class Migration(migrations.Migration):
    dependencies = [
        ('listings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_districts),
    ]
