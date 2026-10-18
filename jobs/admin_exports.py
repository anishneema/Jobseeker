import csv
from django.contrib import admin
from django.http import HttpResponse


def csv_export(filename, fields):
    """Export explicit reporting fields, excluding credentials and private notes."""
    @admin.action(description='Export selected records as CSV', permissions=['view'])
    def export(modeladmin, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(fields)
        for row in queryset.values_list(*fields).iterator():
            safe_row = []
            for value in row:
                text = '' if value is None else str(value)
                if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')):
                    text = "'" + text
                safe_row.append(text)
            writer.writerow(safe_row)
        return response
    export.__name__ = 'export_csv'
    return export
