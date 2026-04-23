class NotFoundError(Exception):
    """Exception untuk data yang tidak ditemukan."""
    pass

class BusinessRuleViolationError(Exception):
    """Exception untuk pelanggaran aturan bisnis (misal: stok habis, toko tutup)."""
    pass

class PermissionDeniedError(Exception):
    """Exception untuk pelanggaran hak akses (misal: mengedit toko orang lain)."""
    pass