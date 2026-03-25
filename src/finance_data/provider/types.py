# Re-export from interface layer for backward compatibility.
# New code should import from finance_data.interface.types directly.
from finance_data.interface.types import DataResult, DataFetchError, ErrorKind  # noqa: F401
