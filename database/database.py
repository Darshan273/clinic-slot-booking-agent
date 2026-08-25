#sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config



engine=create_engine(config("DATABASE_URL"))

sessionlocal=sessionmaker(bind=engine,
                        autocommit=False, 
                        autoflush=False,
                        )

Base = declarative_base()

def get_db():
    db=sessionlocal()
    try:
        yield db
    finally:
        db.close()
