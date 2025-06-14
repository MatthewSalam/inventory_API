from fastapi import FastAPI
from database import engine
import model_folder.model as model
from route_folder import category, payment, product, role, staff, user, order, orderdetail, supplier
from util import auth

app = FastAPI()
model.Base.metadata.create_all(bind=engine)

app.include_router(auth.app, prefix="/auth", tags=["Auth"])
app.include_router(role.router, prefix="/roles", tags=["Roles"])
app.include_router(category.router, prefix="/categories", tags=["Categories"])
app.include_router(payment.router, prefix="/payments", tags=["Payments"])
app.include_router(staff.router, prefix="/staffs", tags=["Staff"])
app.include_router(supplier.router, prefix="/suppliers", tags=["Supplier"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(product.router, prefix="/products", tags=["Products"])
app.include_router(order.router, prefix="/orders", tags=["Order"])
app.include_router(orderdetail.router, prefix="/orderdetails", tags=["OrderDetails"])
