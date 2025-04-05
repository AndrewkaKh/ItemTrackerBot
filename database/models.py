from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    role = Column(String, default="user")
    expenses = Column(Float, default=0.0)
    created_at = Column(Date)
    first_name = Column(String, default="admin")
    second_name = Column(String, default="admin")

class SemiFinishedProduct(Base):
    __tablename__ = 'semi_finished_products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    responsible = Column(String, nullable=False)
    comment = Column(String, nullable=True)

class Stock(Base):
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article = Column(String, nullable=False)
    name = Column(String, nullable=False)
    in_stock = Column(Integer, default=0)
    cost = Column(Float, nullable=False)

class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    article = Column(String, nullable=False)
    name = Column(String, nullable=False)
    incoming = Column(Integer, default=0)
    outgoing = Column(Integer, default=0)
    comment = Column(String)

class ProductComposition(Base):
    __tablename__ = "product_composition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_article = Column(String, nullable=False, unique=True)
    product_name = Column(String, nullable=False)

    components = relationship("ProductComponent", back_populates="product")

class ProductComponent(Base):
    __tablename__ = "product_component"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_article = Column(String, ForeignKey("product_composition.product_article"), nullable=False)
    semi_product_article = Column(String, ForeignKey("semi_finished_products.article"), nullable=False)
    quantity = Column(Integer, nullable=False)

    product = relationship("ProductComposition", back_populates="components")