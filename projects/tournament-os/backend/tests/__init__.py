import os
os.environ["TOURNAMENT_OS_TESTING"] = "true"
import sqlalchemy
from sqlalchemy.schema import DropTable
from sqlalchemy.ext.compiler import compiles

# When running tests against PostgreSQL, we force DROP TABLE ... CASCADE
# to handle circular foreign key dependencies.
@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return f"DROP TABLE {compiler.preparer.format_table(element.element)} CASCADE"

# Save the original create_engine function
original_create_engine = sqlalchemy.create_engine

def monkeypatched_create_engine(*args, **kwargs):
    test_db_url = os.getenv("TOURNAMENT_OS_DATABASE_URL")
    if test_db_url and test_db_url.startswith("postgresql"):
        url = args[0] if args else kwargs.get("url")
        if isinstance(url, str) and "sqlite" in url:
            new_args = list(args)
            if new_args:
                new_args[0] = test_db_url
            else:
                kwargs["url"] = test_db_url
            
            # Remove SQLite-specific kwargs to prevent SQLAlchemy exceptions on Postgres
            kwargs.pop("connect_args", None)
            kwargs.pop("poolclass", None)
            print(f"--> REDIRECTING TEST ENGINE TO POSTGRES: {test_db_url} (intercepted {url})")
            return original_create_engine(*new_args, **kwargs)
    return original_create_engine(*args, **kwargs)

# Install monkeypatch globally for the tests execution
sqlalchemy.create_engine = monkeypatched_create_engine
