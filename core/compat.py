"""
Runtime compatibility shims.

Python 3.14 changed how ``copy.copy()`` treats ``super`` objects, which breaks
Django 4.2's ``BaseContext.__copy__`` (it does ``duplicate = copy(super())``).
The result is an ``AttributeError: 'super' object has no attribute 'dicts'`` that
surfaces on every template that copies its context — in practice, every admin
changelist page 500s.

This patch replaces ``BaseContext.__copy__`` with a version that copies the
instance directly instead of round-tripping through ``copy(super())``. It is a
no-op on Python < 3.14 and on Django releases that have already fixed this.
"""
import sys


def apply_template_context_copy_patch():
    # Only needed on Python 3.14+, where copy(super()) regressed.
    if sys.version_info < (3, 14):
        return

    from django.template import context as _context

    def __copy__(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    _context.BaseContext.__copy__ = __copy__
