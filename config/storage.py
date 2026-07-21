from whitenoise.storage import CompressedManifestStaticFilesStorage


class LenientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Like WhiteNoise's manifest storage, but non-strict.

    django-jazzmin's admin template references `{% static 'vendor/bootswatch' %}`
    (a directory, not a file) just to build a data-attribute prefix for its
    client-side theme switcher. Strict manifest storage raises on that missing
    entry; non-strict falls back to the unhashed path instead of crashing.
    """

    manifest_strict = False
