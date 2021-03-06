import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(80), unique=True, nullable=False)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category = relationship(Category)
    update_at = Column(DateTime,
                       default=datetime.datetime.now,
                       onupdate=datetime.datetime.now)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id,
            'update_at': self.update_at,
        }


engine = create_engine('postgresql://vagrant:123@localhost:5432/catalog')

Base.metadata.create_all(engine)

if __name__ == "__main__":
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    category = Category(
        name="Soccer"
    )
    session.add(category)
    category = Category(
        name="Basketball"
    )
    session.add(category)
    category = Category(
        name="Baseball"
    )
    session.add(category)
    category = Category(
        name="Football"
    )
    session.add(category)
    category = Category(
        name="Hockey"
    )
    session.add(category)
    category = Category(
        name="Skating"
    )
    session.add(category)
    session.commit()
