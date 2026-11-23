from collections import Counter
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Pizza Orders API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orders", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderIn, db: Session = Depends(get_db)):
    order = models.Order(
        customer_name=payload.customer_name,
        items=[models.OrderItem(**item.model_dump()) for item in payload.items],
    )
    if payload.created_at is not None:
        order.created_at = payload.created_at
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(models.Order).order_by(models.Order.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(models.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(models.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()


@app.get("/analytics/summary", response_model=schemas.Summary)
def summary(db: Session = Depends(get_db)):
    order_count = db.scalar(select(func.count(models.Order.id))) or 0
    revenue = db.scalar(
        select(func.coalesce(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price), 0))
    )
    revenue = round(float(revenue), 2)
    average = round(revenue / order_count, 2) if order_count else 0.0
    return schemas.Summary(
        order_count=order_count, total_revenue=revenue, average_order_value=average
    )


@app.get("/analytics/peak-hours", response_model=list[schemas.HourStat])
def peak_hours(db: Session = Depends(get_db)):
    created = db.scalars(select(models.Order.created_at)).all()
    counts = Counter(ts.hour for ts in created)
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [schemas.HourStat(hour=hour, orders=orders) for hour, orders in ranked]
