import databases
import sqlalchemy
import os

DATABASE_URL = os.getenv("DATABASE_URL=postgresql://orcamentos_db_rbu2_user:kyJTDIF17H4E6hac3bQ57d5r6Xa6Uw5r@dpg-d3ofpq6r433s73a2eag0-a/orcamentos_db_rbu2")

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

# A linha 'connect_args' foi removida daqui
engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)
