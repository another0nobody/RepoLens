"""订单 REST 接口。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.order_service import create_order, get_order

router = APIRouter(tags=["orders"])


class OrderCreate(BaseModel):
    customer_name: str = Field(description="客户姓名")
    amount: float = Field(gt=0, description="订单金额")


@router.get("/orders/{order_id}")
def read_order(order_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return get_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/orders")
def add_order(payload: OrderCreate, db: Session = Depends(get_db)) -> dict:
    order = create_order(db, payload.customer_name, payload.amount)
    return {"id": order.id, "status": order.status}
