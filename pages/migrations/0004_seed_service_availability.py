from django.db import migrations

# The items that were hard-coded in serving_areas.html / area_detail.html.
ITEMS = [
    ('ti-truck',         'Doorstep Delivery', 'Fast delivery right to your door'),
    ('ti-tool',          'Installation',      'Professional setup by trained technicians'),
    ('ti-device-mobile', 'Device Repair',     'Repairs for phones, laptops and TVs'),
    ('ti-shield-check',  'Warranty Support',  'Help with brand warranty claims'),
    ('ti-headset',       'Local Support',     'A local team you can call'),
]


def seed(apps, schema_editor):
    Item = apps.get_model('pages', 'ServiceAvailability')
    if Item.objects.exists():
        return
    Item.objects.bulk_create(
        Item(icon=icon, title=title, description=desc, order=i)
        for i, (icon, title, desc) in enumerate(ITEMS)
    )


def unseed(apps, schema_editor):
    apps.get_model('pages', 'ServiceAvailability').objects.filter(
        title__in=[t for _, t, _ in ITEMS]).delete()


class Migration(migrations.Migration):
    dependencies = [('pages', '0003_service_availability')]
    operations = [migrations.RunPython(seed, unseed)]
