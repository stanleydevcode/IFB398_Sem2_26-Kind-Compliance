"""Empty frontend view models while database-backed modules are being built."""


def page_context():
    return dict(workers=[], participants=[])
