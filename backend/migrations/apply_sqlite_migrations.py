import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).parent
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "team.db"


def apply_migrations() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    msg = str(exc).lower()
                    if "duplicate column name" in msg or "already exists" in msg:
                        continue
                    raise
            conn.commit()
            print(f"applied {sql_file.name}")


if __name__ == "__main__":
    apply_migrations()
