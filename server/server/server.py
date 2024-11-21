import csv
import glob
import hashlib
import logging
import os
import subprocess
import zipfile
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

import instructor
from tenacity import Retrying, stop_after_attempt
from anthropic import Anthropic
from openai import OpenAI

from bson.binary import Binary
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pymongo import MongoClient
from pymongo.database import Database

from .settings import DATA_STORAGE_PATH, MONGO_URI, LLM_PROVIDER
from .prompt import BILL_SPLIT_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Outputs to console
        logging.FileHandler("server.log"),  # Outputs to file
    ],
)

logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:80",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_mongodb() -> Database:
    client: MongoClient = MongoClient(MONGO_URI)
    db: Database = client.get_default_database()
    return db

class LLMClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: instructor.Instructor
    model: str

async def get_llm() -> LLMClient:
    if LLM_PROVIDER == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
            
        # Use instructor to patch Anthropic client
        client = instructor.from_anthropic(Anthropic(api_key=api_key))
        model = "claude-3-opus-20240229"
    elif LLM_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set OPENAI_API_KEY environment variable")
            
        # Use instructor to patch OpenAI client
        client = instructor.from_openai(OpenAI(api_key=api_key))
        # model = "gpt-4o-mini"
        model = "gpt-4o"
    else:
        raise ValueError(f"Unknown provider: {LLM_PROVIDER}")

    # instructor.patch(
    #     client,
    #     mode=instructor.Mode.TOOLS,
    #     max_retries=3,           # Number of retries
    #     retry_delay=1,           # Delay between retries in seconds
    #     timeout=25,              # Total timeout in seconds
    #     retry_exceptions=[       # List of exceptions to retry on
    #         ValueError,
    #         KeyError,
    #         JSONDecodeError,
    #         instructor.errors.ParsingError,
    #     ]
    # )

    return LLMClient(
        client=client,
        model=model,   
    )

class BillItem(BaseModel):
    items: Dict[str, float] = Field(..., description="A dictionary with item names as keys and their prices as values.")
    currency: str = Field(..., description="The currency shorthand, for example Rupees, Dollars, etc.")

class Person(BaseModel):
    people: List[str] = Field(..., description="A list of people names involved in the bill.")

class Mapping(BaseModel):
    assignment: Dict[str, List[str]] = Field(..., description="A mapping from each person's name to a list of items they are responsible for.")

class SplitBill(BaseModel):
    bill_item: BillItem
    person: Person
    mapping: Mapping

class PersonAmount(BaseModel):
    name: str = Field(..., description="Name of the person")
    amount: float = Field(..., description="Amount to be paid by the person")
    shared_items: List[str] = Field(..., description="List of items shared by this person")

class BillSplitCalculation(BaseModel):
    per_person_split: List[PersonAmount] = Field(..., description="List of per-person bill splits")
    total_amount: float = Field(..., description="Total bill amount")
    shared_item_counts: Dict[str, int] = Field(..., description="Number of people sharing each item")


class SplitBillResponse(BaseModel):
    status: str
    split_bill: Optional[SplitBill]
    calculation: Optional[BillSplitCalculation]


@app.post("/api/split_bill")
async def split_bill(
    user_bill_context: str = File(..., description="Text context for the bill"),
    image: UploadFile = File(..., description="Image file of the bill"),
    llm: LLMClient = Depends(get_llm),
) -> SplitBillResponse:
    try:
        # Read and encode the image file as base64
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        retries = Retrying(
            stop=stop_after_attempt(5)
        )


        # Prepare image data based on the LLM provider
        if llm.model.startswith("claude"):
            image_data = {
                "type": "image", 
                "source": {
                    "type": "base64",
                    "media_type": image.content_type,
                    "data": image_base64,
                },
            }
        elif llm.model.startswith("gpt"):
            image_data = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_base64}",
                },
            }
        else:
            raise ValueError(f"Unsupported model: {llm.model}")

        logging.info(f'Using model: {llm.model}')

        # Create the message payload for the LLM
        split_bill = llm.client.messages.create(
            model=llm.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": BILL_SPLIT_PROMPT},
                        {"type": "text", "text": user_bill_context},
                        image_data,
                    ],
                }
            ],
            response_model=SplitBill,
            max_retries=retries,
        )

        # Calculate bill splits
        bill = split_bill.bill_item.items
        people = split_bill.person.people
        mapping = split_bill.mapping.assignment

        # Validate data
        assert set(people) == set(mapping.keys())

        all_items = set()
        for name in mapping:
            mapping_item_list = mapping[name]
            for i in mapping_item_list:
                all_items.add(i)

        assert all_items == set(bill.keys())

        # Calculate item sharing counts
        item_sharing = {item: 0 for item in bill}
        for name, items in mapping.items():
            for item in items:
                item_sharing[item] += 1

        # Calculate per person amounts
        per_person_splits = []
        total_amount = 0.0

        for name in mapping:
            item_list = mapping[name]
            amount = 0.0
            for item in item_list:
                amount += bill[item] / item_sharing[item]
            total_amount += amount
            per_person_splits.append(
                PersonAmount(
                    name=name,
                    amount=round(amount, 2),
                    shared_items=item_list
                )
            )

        calculation = BillSplitCalculation(
            per_person_split=per_person_splits,
            total_amount=round(total_amount, 2),
            shared_item_counts=item_sharing
        )

        return SplitBillResponse(
            status="ok",
            split_bill=split_bill,
            calculation=calculation
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        import traceback
        logger.error(f"Error processing request: {traceback.format_exc()}")
        return SplitBillResponse(
            status="error",
            split_bill=None,
            calculation=None,
        )


class HeartbeatResponse(BaseModel):
    status: str


@app.post("/api/heartbeat")
async def upload_data(
    db: Database = Depends(get_mongodb),
) -> HeartbeatResponse:
    try:
        # Attempt to run a simple command to check MongoDB connection
        await db.command("ping")
        logger.info("heartbeat ok")
        return HeartbeatResponse(status="ok")
    except Exception as e:
        logger.error(f"MongoDB error: {e}")
        return HeartbeatResponse(status="mongo error")
    

# Mount the static files directory
os.makedirs(DATA_STORAGE_PATH, exist_ok=True)
app.mount("/data", StaticFiles(directory=DATA_STORAGE_PATH), name="data")

# Add a catch-all route for serving files from DATA_STORAGE_PATH
@app.get("/data/{file_path:path}")
async def serve_file(file_path: str):
    full_path = os.path.join(DATA_STORAGE_PATH, file_path)
    logger.info("full_path: " + str(full_path))
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")
