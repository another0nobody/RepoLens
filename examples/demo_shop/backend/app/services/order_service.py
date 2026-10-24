"""订单业务逻辑：查数据库 + 写 Redis 缓存。"""

import json

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order

cache = redis.Redis(host="localhost", port=6379, decode_responses=True)


def get_order(db: Session, order_id: int) -> dict:
    """先查缓存，未命中再查 PostgreSQL，并回填缓存。"""
    cached = cache.get(f"order:{order_id}")
    if cached:
        return json.loads(cached)

    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise ValueError(f"订单不存在: {order_id}")

    payload = {
        "id": order.id,
        "customer_name": order.customer_name,
        "amount": order.amount,
        "status": order.status,
    }
    cache.setex(f"order:{order_id}", 300, json.dumps(payload, ensure_ascii=False))
    return payload


def create_order(db: Session, customer_name: str, amount: float) -> Order:
    order = Order(customer_name=customer_name, amount=amount)
    db.add(order)
    db.commit()
    db.refresh(order)
    cache.delete(f"order:{order.id}")
    return order
