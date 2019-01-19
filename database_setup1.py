from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class MakeUp(Base):
    __tablename__ = 'makeup'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            }


class MakeUpItem(Base):
    __tablename__ = 'makeup_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    group = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))
    makeup_id = Column(Integer, ForeignKey('makeup.id'))
    makeup = relationship(MakeUp)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'group': self.group,
            'description': self.description,
            'price': self.price,
            }

engine = create_engine('sqlite:///makeupcatalog.db')


Base.metadata.create_all(engine)
