from sqlalchemy import inspect

import app.models
from app.db.base import Base
from app.db.session import engine


def main() -> None:
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\nDatabase tables created successfully:")

    for table in sorted(tables):
        print(f"  - {table}")

    print(f"\nTotal tables: {len(tables)}")


if __name__ == "__main__":
    main()