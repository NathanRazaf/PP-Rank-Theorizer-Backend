from fastapi import FastAPI
from userRouter import main_data_router
app = FastAPI()

app.include_router(main_data_router, prefix="/user")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
