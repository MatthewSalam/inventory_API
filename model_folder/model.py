from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base =  declarative_base()

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    name = Column(String, unique=True)
    description = Column(String, unique=True)

    products = relationship("Product", back_populates="category")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    description = Column(String)

    staff = relationship("Staff", back_populates="role")

class Payment(Base):
    __tablename__ = "payments"
    bill_number = Column(Integer, primary_key=True,index=True)
    payment_type = Column(String)
    is_active = Column(Boolean, default=True)
    other_details = Column(String)

    order_detail = relationship("Order_Detail", back_populates="payment")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String,)
    address = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    fax = Column(Integer, unique=True)
    email = Column(String, unique=True)
    other_details = Column(String)

    products = relationship("Product", back_populates="supplier")

class Staff(Base):
    __tablename__ = "staffs"
    id = Column(Integer, primary_key=True, index=True)
    lastname = Column(String)
    firstname = Column(String)
    address = Column(String)
    is_active = Column(Boolean, default=True)
    username = Column(String)
    email = Column(String, unique=True)
    password = Column(String, unique=True)
    phone = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="staff")
    users = relationship("User", back_populates="staff")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    lastname = Column(String)
    firstname = Column(String)
    is_active = Column(Boolean, default=True)
    email = Column(String, unique=True)
    phone = Column(String)
    staff_id = Column(Integer, ForeignKey("staffs.id"))

    staff = relationship("Staff", back_populates="users")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    desc = Column(String)
    unit = Column(Integer)
    other_details = Column(String)
    price = Column(Float)
    cat_id = Column(Integer, ForeignKey("categories.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    status = Column(String, default="Available")

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    order_details = relationship("Order_Detail", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    detail = Column(String)
    is_active = Column(Boolean, default=True)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)

    order_details = relationship("Order_Detail", back_populates="order")

class Order_Detail(Base):
    __tablename__ = "order_details"
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    bill_number = Column(Integer, ForeignKey("payments.bill_number"))
    discount = Column(Float)
    total = Column(Float)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product", back_populates="order_details")
    payment = relationship("Payment", back_populates="order_detail")