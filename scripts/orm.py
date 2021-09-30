from sqlalchemy import create_engine, Integer, Column, Text, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite://", echo=True)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


# Using declarative
class Record(Base):
    __tablename__ = "log"
    __table_args__ = {"sqlite_autoincrement": True}
    sn = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    body = Column(Integer)


Base.metadata.create_all(engine)

with session.begin():
    print(session.add(Record(body="hello")))
    print(session.add(Record(body="world")))
    print(session.add(Record(sn=8, body="system")))
    print(session.add(Record(sn=4, body="galaxy")))
    print(session.add(Record(body="universe")))
with session.begin():
    print(session.query(Record.sn, Record.body).order_by(Record.sn).all())
try:
    with session.begin():
        print(session.add(Record(sn=8, body="duplicate")))
    print("Ruh roh, a duplicate SN was allowed.")
except IntegrityError as err:
    print("SQLite checked for errors!")

print("Ran ORM!")