import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "warehouse" / "cpg.duckdb"


@pytest.fixture(scope="session")
def con():
    """Read-only connection to the built warehouse; tests needing data skip if it was not built."""
    if not DB.exists():
        pytest.skip("warehouse not built - run `make all` first")
    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()
