"""Product id parsing and the side-by-side comparison table.

Shared by the compare / wishlist pages and the API (GET /api/v1/products/compare/).
"""
import uuid

from django.db.models import Avg, Count, Q

from .models import Product

MAX_COMPARE = 3


def parse_ids(raw_values, limit):
    """Valid, de-duplicated product UUIDs in the order given (at most `limit`).

    pk is a UUID, so a malformed value would raise ValidationError (500) inside a
    queryset; junk is skipped instead. Accepts repeated and comma-separated values.
    """
    ids = []
    for raw in raw_values:
        for part in str(raw).split(','):
            try:
                pk = uuid.UUID(part.strip())
            except ValueError:
                continue
            if pk not in ids:
                ids.append(pk)
    return ids[:limit]


def build_comparison(ids, blank='—'):
    """The comparison for products `ids` (kept in that order).

    Row values the product has none for are `blank`; rows no product has a
    value for are dropped.
    """
    found = {p.pk: p for p in (Product.objects.filter(pk__in=ids, is_active=True)
                               .select_related('category', 'brand')
                               .prefetch_related('images', 'attributes__attribute')
                               .annotate(avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                                         num_reviews=Count('reviews', filter=Q(reviews__is_approved=True))))}
    products = [found[pk] for pk in ids if pk in found]   # keep the user's selection order

    for p in products:
        p.avg_rating = round(p.avg_rating or 0, 1)
        imgs = list(p.images.all())                        # prefetched — no extra queries
        p.cover = next((i for i in imgs if i.is_primary), imgs[0] if imgs else None)

    def row(label, values):
        vals = [v if v not in (None, '') else blank for v in values]
        return {'label': label, 'values': vals, 'differs': len({str(v) for v in vals}) > 1}

    general = [
        row('Brand',     [p.brand.name if p.brand else None for p in products]),
        row('Category',  [p.category.name for p in products]),
        row('Condition', [p.get_condition_display() for p in products]),
        row('Warranty',  [p.warranty for p in products]),
        row('Color',     [p.color for p in products]),
        row('Weight',    [f'{p.weight.normalize():f} kg' if p.weight else None for p in products]),
        row('SKU',       [p.sku for p in products]),
    ]
    # Rows no product has a value for add nothing to a comparison.
    general = [r for r in general if any(v != blank for v in r['values'])]

    attr_maps = [{av.attribute.name: av.value for av in p.attributes.all()} for p in products]
    all_attrs = sorted({name for m in attr_maps for name in m})
    specs     = [row(name, [m.get(name) for m in attr_maps]) for name in all_attrs]

    prices = [p.effective_price for p in products]
    return {
        'products':      products,
        'general_rows':  general,
        'spec_rows':     specs,
        'best_price':    min(prices) if len(products) > 1 else None,
        'price_differs': len(set(prices)) > 1,
    }
