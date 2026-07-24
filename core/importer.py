"""
Reusable spreadsheet-import engine for the admin (CSV + optional XLSX).

Drop :class:`SpreadsheetImportMixin` onto any ``ModelAdmin`` and implement
``import_row(row, request)`` to gain:

* an **Import** button on the changelist (``object-tools``),
* an upload page with inline instructions and a one-click sample-CSV download,
* CSV parsing out of the box, plus ``.xlsx`` parsing when ``openpyxl`` is
  installed (it degrades gracefully with a clear message if it is not),
* per-row error reporting so one bad row never aborts the whole import.

The engine is intentionally dependency-light: CSV uses the stdlib, so the
feature works on a bare checkout. ``openpyxl`` is listed in requirements.txt
for Excel support but is imported lazily.
"""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse


# ── Value parsing helpers ──────────────────────────────────────────────────

_TRUE  = {'1', 'true', 't', 'yes', 'y', 'on', 'active'}
_FALSE = {'0', 'false', 'f', 'no', 'n', 'off', 'inactive', ''}


def parse_bool(value, default=False):
    """Loosely parse a spreadsheet cell into a bool (blank -> ``default``)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return default


def parse_decimal(value, field='value'):
    """Parse a currency/number cell into ``Decimal`` (blank -> ``None``)."""
    if value is None:
        return None
    s = str(value).strip().replace(',', '').replace('₹', '').replace('$', '')
    if s == '':
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f'{field}: "{value}" is not a valid number')


def parse_int(value, field='value', default=None):
    """Parse an integer cell (blank -> ``default``)."""
    if value is None:
        return default
    s = str(value).strip().replace(',', '')
    if s == '':
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        raise ValueError(f'{field}: "{value}" is not a valid integer')


def clean(value):
    """Return a stripped string for a cell, or '' for blanks/None."""
    if value is None:
        return ''
    return str(value).strip()


# ── File reading ───────────────────────────────────────────────────────────

class ImportError_(Exception):
    """Raised for whole-file problems (bad format, unreadable, no rows)."""


def read_rows(uploaded_file):
    """Return ``list[dict]`` of rows keyed by lower-cased header names.

    Supports ``.csv`` (stdlib) and ``.xlsx`` (via ``openpyxl`` if installed).
    Header names are lower-cased and stripped so mapping is case-insensitive.
    """
    name = (uploaded_file.name or '').lower()
    raw = uploaded_file.read()

    if name.endswith('.xlsx') or name.endswith('.xlsm'):
        return _read_xlsx(raw)
    # Default: treat everything else as CSV (also handles .txt / .tsv-ish).
    return _read_csv(raw)


def _normalize_headers(headers):
    return [clean(h).lower() for h in headers]


def _read_csv(raw: bytes):
    # Tolerate a UTF-8 BOM (Excel "Save as CSV" adds one).
    text = raw.decode('utf-8-sig', errors='replace')
    reader = csv.reader(io.StringIO(text))
    try:
        headers = _normalize_headers(next(reader))
    except StopIteration:
        raise ImportError_('The file is empty.')
    rows = []
    for values in reader:
        if not any(clean(v) for v in values):
            continue  # skip fully blank lines
        row = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
        for h in headers[len(values):]:
            row[h] = ''
        rows.append(row)
    return rows


def _read_xlsx(raw: bytes):
    try:
        import openpyxl  # lazy: optional dependency
    except ImportError:
        raise ImportError_(
            'Excel (.xlsx) support requires the "openpyxl" package. '
            'Install it with "pip install openpyxl", or upload a .csv file instead.'
        )
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        headers = _normalize_headers(next(rows_iter))
    except StopIteration:
        raise ImportError_('The spreadsheet is empty.')
    rows = []
    for values in rows_iter:
        if values is None or not any(clean(v) for v in values):
            continue
        row = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
        for h in headers[len(values):]:
            row[h] = ''
        rows.append(row)
    return rows


# ── Admin mixin ────────────────────────────────────────────────────────────

class SpreadsheetImportMixin:
    """Adds a spreadsheet-import workflow to a ``ModelAdmin``.

    Subclasses must define:

    * ``import_columns``   – list of ``(name, required, help)`` tuples used to
      render instructions and build the sample CSV.
    * ``import_row(row, request)`` – process one row dict; return the string
      ``'created'`` or ``'updated'``, or raise ``ValueError`` for a row-level
      problem (the row is skipped and the message is shown to the user).

    Optional:

    * ``import_title``     – heading shown on the upload page.
    * ``import_intro``     – short paragraph of guidance.
    * ``import_sample_row``– dict of example values for the sample CSV.
    """

    change_list_template = 'admin/spreadsheet_change_list.html'
    import_columns: list = []
    import_title = 'Import from spreadsheet'
    import_intro = ''
    import_sample_row: dict = {}

    # ── URL wiring ─────────────────────────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path('import/', self.admin_site.admin_view(self.import_view),
                 name='%s_%s_import' % info),
            path('import/sample.csv', self.admin_site.admin_view(self.import_sample_csv),
                 name='%s_%s_import_sample' % info),
        ]
        return custom + urls

    def _url(self, suffix):
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse('admin:%s_%s_%s' % (info + (suffix,)))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['spreadsheet_import_url'] = self._url('import')
        return super().changelist_view(request, extra_context)

    # ── The upload page ────────────────────────────────────────────
    def import_view(self, request):
        opts = self.model._meta
        context = {
            **self.admin_site.each_context(request),
            'opts': opts,
            'title': self.import_title,
            'intro': self.import_intro,
            'columns': self.import_columns,
            'sample_url': self._url('import_sample'),
            'changelist_url': self._url('changelist'),
            'media': self.media,
        }

        if request.method == 'POST':
            upload = request.FILES.get('spreadsheet')
            if not upload:
                self.message_user(request, 'Please choose a CSV or XLSX file to upload.',
                                  level=messages.ERROR)
                return redirect(request.path)

            dry_run = bool(request.POST.get('dry_run'))
            try:
                rows = read_rows(upload)
            except ImportError_ as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
                return redirect(request.path)

            if not rows:
                self.message_user(request, 'No data rows found in the file.',
                                  level=messages.WARNING)
                return redirect(request.path)

            created, updated, errors = self._process_rows(rows, request, dry_run)

            # Report outcome.
            if dry_run:
                self.message_user(
                    request,
                    f'Dry run: {created} would be created, {updated} would be updated, '
                    f'{len(errors)} row(s) had errors. Nothing was saved.',
                    level=messages.INFO if not errors else messages.WARNING,
                )
            else:
                if created or updated:
                    self.message_user(
                        request,
                        f'Import complete: {created} created, {updated} updated.',
                        level=messages.SUCCESS,
                    )
                if not created and not updated and not errors:
                    self.message_user(request, 'Nothing to import.', level=messages.WARNING)

            for msg in errors[:25]:
                self.message_user(request, msg, level=messages.ERROR)
            if len(errors) > 25:
                self.message_user(request, f'…and {len(errors) - 25} more error(s).',
                                  level=messages.ERROR)

            if not dry_run and (created or updated):
                return redirect(self._url('changelist'))
            return redirect(request.path)

        return TemplateResponse(request, 'admin/import_spreadsheet.html', context)

    def _process_rows(self, rows, request, dry_run):
        """Run every row inside one transaction.

        On a real run each good row is committed and bad rows are skipped;
        on a dry run the whole transaction is rolled back so nothing persists.
        """
        from django.db import transaction

        created = updated = 0
        errors = []
        with transaction.atomic():
            for i, row in enumerate(rows, start=2):  # row 1 = header
                # Each row gets a savepoint so a failure rolls back only that row.
                try:
                    with transaction.atomic():
                        result = self.import_row(row, request)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                except ValueError as exc:
                    errors.append(f'Row {i}: {exc}')
                except Exception as exc:  # pragma: no cover - defensive
                    errors.append(f'Row {i}: unexpected error — {exc}')
            if dry_run:
                transaction.set_rollback(True)
        return created, updated, errors

    # ── Sample CSV download ────────────────────────────────────────
    def import_sample_csv(self, request):
        headers = [c[0] for c in self.import_columns]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename={self.model._meta.model_name}_import_template.csv'
        )
        writer = csv.writer(response)
        writer.writerow(headers)
        if self.import_sample_row:
            writer.writerow([self.import_sample_row.get(h, '') for h in headers])
        return response
