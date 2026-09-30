"""
Create staff permission groups (Module 11 — User management / roles).

Usage:
    python manage.py setup_roles

Groups created:
  • Catalog Managers — full CRUD on products, categories, brands, variants, images
  • Content Editors  — CMS pages, blog, banners, services, serving areas, FAQs
  • Support Agents   — view + change inquiries and reviews (no delete)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps


ROLES = {
    'Catalog Managers': {
        'products': {
            'category': ['add', 'change', 'delete', 'view'],
            'product': ['add', 'change', 'delete', 'view'],
            'productimage': ['add', 'change', 'delete', 'view'],
            'productvariant': ['add', 'change', 'delete', 'view'],
            'productattribute': ['add', 'change', 'delete', 'view'],
            'productattributevalue': ['add', 'change', 'delete', 'view'],
            'faq': ['add', 'change', 'delete', 'view'],
        },
        'core': {'brand': ['add', 'change', 'delete', 'view']},
    },
    'Content Editors': {
        'blog': {
            'blogpost': ['add', 'change', 'delete', 'view'],
            'blogcategory': ['add', 'change', 'delete', 'view'],
            'blogcomment': ['change', 'delete', 'view'],
        },
        'pages': {
            'flatpage': ['add', 'change', 'delete', 'view'],
            'service': ['add', 'change', 'delete', 'view'],
            'servicefeature': ['add', 'change', 'delete', 'view'],
            'servingarea': ['add', 'change', 'delete', 'view'],
            'faqcategory': ['add', 'change', 'delete', 'view'],
            'generalfaq': ['add', 'change', 'delete', 'view'],
        },
        'core': {
            'banner': ['add', 'change', 'delete', 'view'],
            'testimonial': ['add', 'change', 'delete', 'view'],
            'whychooseus': ['add', 'change', 'delete', 'view'],
        },
    },
    'Support Agents': {
        'core': {'contactinquiry': ['change', 'view']},
        'products': {
            'productinquiry': ['change', 'view'],
            'review': ['change', 'view'],
        },
        'pages': {'serviceinquiry': ['change', 'view']},
    },
}


class Command(BaseCommand):
    help = 'Create/refresh staff permission groups for delegated admin access.'

    def handle(self, *args, **options):
        for group_name, app_models in ROLES.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()
            added = 0
            for app_label, models in app_models.items():
                for model_name, actions in models.items():
                    try:
                        model = apps.get_model(app_label, model_name)
                    except LookupError:
                        self.stderr.write(f'  [skip] unknown model {app_label}.{model_name}')
                        continue
                    ct = ContentType.objects.get_for_model(model)
                    for action in actions:
                        codename = f'{action}_{model_name}'
                        try:
                            perm = Permission.objects.get(content_type=ct, codename=codename)
                            group.permissions.add(perm)
                            added += 1
                        except Permission.DoesNotExist:
                            self.stderr.write(f'  [warn] missing permission {codename}')
            self.stdout.write(self.style.SUCCESS(f'[ok] {group_name}: {added} permissions'))
        self.stdout.write(self.style.SUCCESS(
            'Done. Assign users to these groups in admin > Users, and set is_staff=True.'))
