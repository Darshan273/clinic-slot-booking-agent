from pydantic import BaseModel, Field
from typing import List, TypedDict
from datetime import datetime
from langgraph.graph.message import add_messages
from typing import Annotated


#FASTAPI ENDPOINT PYDANTIC MODELS

class chatrequest(BaseModel):
    session_id:str
    user_message:str

class chatresponse(BaseModel):
    session_id:str
    user_message:str
    
#tool SCHEMAS

class check_availability(BaseModel):
    date: str = Field(
        description="appointment date in YYYY-MM-DD format. Do not include the requested time.",
        examples=["2026-08-25"],
    )


class create_booking(BaseModel):
    start_time: str = Field(
        description="start date and time of the appointment, e.g. YYYY-MM-DD HH:MM:SS",
        examples=["2026-07-16 18:30:00"],
    )
    name: str = Field(
        description="name of the patient",
        examples=["Darshan"],
    )
    email: str = Field(
        description="email of the patient",
        examples=["[EMAIL_ADDRESS]"],
    )
    reason: str = Field(
        description="reason for the appointment",
        examples=["fever, headache, flu, follow-up checkup"],
    )
    
#graph pydantic schema

class GraphState(TypedDict):
    messages:Annotated[List, add_messages]

#get conversatation history

class ConversationResponse(BaseModel):
    id: int
    session_id: str
    human_message: str
    ai_message: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


    
