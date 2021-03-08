import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

db_session = None
Base = None


def init_db_develop():
    from coffeetag.model import User, Drink
    user = User(tag=b'5', name='Hackenberg', prename='Stefan')
    db_session.add(user)
    db_session.add(Drink(user=user))
    db_session.commit()


def init_db():
    global db_session
    if db_session is not None:
        return db_session

    from coffeetag import app
    if app.config['ENV'] == 'development' or app.testing:
        engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool, echo=True)
    else:
        engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)

    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    global Base
    Base = declarative_base()
    Base.query = db_session.query_property()

    import coffeetag.model
    Base.metadata.create_all(bind=engine)

    if app.config['ENV'] == 'development':
        init_db_develop()
    return db_session
