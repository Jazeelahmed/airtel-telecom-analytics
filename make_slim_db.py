import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
SOURCES = [HERE / "data" / "raw" / "airtel.db", HERE / "airtel.db"]
DEST = HERE / "airtel_slim.db"
TABLES = ["customers", "plans", "circles", "recharges", "complaints"]

src = next((p for p in SOURCES if p.exists() and p.stat().st_size > 1_000_000), None)
if src is None:
    raise SystemExit("Full airtel.db not found (expected data/raw/airtel.db).")

if DEST.exists():
    DEST.unlink()

con = sqlite3.connect(DEST)
con.execute("ATTACH DATABASE ? AS full", (str(src),))
for t in TABLES:
    ddl = con.execute("SELECT sql FROM full.sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
    if ddl is None:
        raise SystemExit(f"Table '{t}' missing in {src}")
    con.execute(ddl[0])
    con.execute(f'INSERT INTO main."{t}" SELECT * FROM full."{t}"')
    n = con.execute(f'SELECT COUNT(*) FROM main."{t}"').fetchone()[0]
    print(f"{t}: {n:,} rows")
con.commit()
con.execute("DETACH DATABASE full")
con.execute("VACUUM")
con.close()
print(f"\nCreated {DEST.name}: {DEST.stat().st_size / 1_048_576:.1f} MB")