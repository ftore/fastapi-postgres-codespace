from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import Restaurant, create_db_engine

app = FastAPI()


# Pydantic model
class RestaurantIn(BaseModel):
    name: str
    address: Union[str, None] = None


engine = create_db_engine(echo=True)

# Tables are created by Alembic: run `poetry run alembic upgrade head`


@app.get("/")
def root():
    return "Welcome to the FastAPI and Postgres in a dev container demonstration. Add /docs to the URL to see API methods."


@app.get("/restaurant/{id}")
def get_restaurant(id: int):
    with Session(engine) as session:
        query = select(Restaurant).where(Restaurant.id == id)
        restaurants = session.execute(query).scalars().all()
        return f"{restaurants[0].id}, {restaurants[0].name}, {restaurants[0].address}"


@app.post("/restaurant")
def set_restaurant(item: RestaurantIn):
    with Session(engine) as session:
        restaurant = Restaurant(name=item.name, address=item.address)
        session.add(restaurant)
        session.commit()
        return f"Added restaurant with id {restaurant.id}."


@app.get("/all")
def get_all_restaurants():
    rows = []
    with Session(engine) as session:
        resturants = session.query(Restaurant).all()
        for restaurant in resturants:
            rows.append(f"{restaurant.id}, {restaurant.name}, {restaurant.address}")
    return rows
