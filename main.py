from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from  pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware # Required for frontend integration

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI) # To Make api prod grade

db = client["warehouse_db"]
collection = db["items"]

app = FastAPI()

origins = ["*"] # Allow all origins for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

class Product_desc(BaseModel):
    product_id : int
    product_name: str
    quantity: int
    price: float
    date_of_manufacture: str
    date_of_expiry: str

@app.get("/")
def serve_home():
    with open("static/index.html") as file:
        return HTMLResponse(content=file.read())
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/warehouse/add_item") 
async def add_item(data:Product_desc): 
    result = await collection.insert_one(data.dict()) 
    return {"msg":"Item added successfully","product_id": data.product_id}


def euron_helper(doc):
    doc["id"] = str(doc["_id"]) # Removes id and returns everything else
    del doc["_id"]
    return doc

@app.get("/warehouse/getdata")
async def get_euron_data():
    iterms = []
    cursor = collection.find({})
    async for document in cursor:
        iterms.append(euron_helper(document))
    return iterms

@app.put("/warehouse/update/{product_id}")
async def update_product_id(product_id:int):
    updated_data = await collection.update_one(
    {"product_id": product_id},
    {"$set": {"price": 999}}
)
    if updated_data.modified_count == 1:
        return {"msg":"Data updated successfully"}
    else:
        raise HTTPException(status_code = 404 , detail = "Data not found")
    

@app.delete("/warehouse/delete/{product_id}")
async def delete_product(product_id:int):
    result = await collection.delete_one({"product_id": product_id})
    if result.deleted_count == 1:
        return {"msg": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@app.patch("/warehouse/patch/{product_id}")
async def patch_warehouse_item(product_id:int, data:Product_desc):
    updated_data = {}
    for key, value in data.dict().items():
        if value is not None:
            updated_data[key] = value
    if updated_data:
        result = await collection.update_one({"product_id": product_id}, {"$set": updated_data})
        if result.modified_count == 1:
            return {"msg": "Data patched successfully"}
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    raise HTTPException(status_code=400, detail="No data provided for update")