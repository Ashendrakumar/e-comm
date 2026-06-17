"""Reusable admin mixins (Module 11)."""
import csv
from django.http import HttpResponse


class ExportCsvMixin:
    """Adds an 'Export selected to CSV' admin action.

    Set ``csv_export_fields`` on the ModelAdmin to control columns;
    defaults to all concrete model fields.
    """
    csv_export_fields = None

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = self.csv_export_fields or [f.name for f in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, f) for f in field_names])
        self.message_user(request, f'Exported {queryset.count()} row(s) to CSV.')
        return response

    export_as_csv.short_description = 'Export selected to CSV'
