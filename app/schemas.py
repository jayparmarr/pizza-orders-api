from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    pizza: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=100)
    unit_price: float = Field(gt=0, le=10000)


class OrderIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str = Field(min_length=1, max_length=100)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    created_at: datetime | None = None


class OrderItemOut(OrderItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    created_at: datetime
    items: list[OrderItemOut]
    total: float


class Summary(BaseModel):
    order_count: int
    total_revenue: float
    average_order_value: float


class HourStat(BaseModel):
    hour: int
    orders: int
