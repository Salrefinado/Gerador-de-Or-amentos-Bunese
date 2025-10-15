import databases
import sqlalchemy

DATABASE_URL = "sqlite:///./orcamentos.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

orcamentos = sqlalchemy.Table(
    "orcamentos",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("numero", sqlalchemy.String),
    sqlalchemy.Column("cliente", sqlalchemy.String),
    sqlalchemy.Column("data_atualizacao", sqlalchemy.String),
    sqlalchemy.Column("dados", sqlalchemy.JSON),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)