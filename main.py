#fastapi endpoint
from fastapi import HTTPException
from contextlib import asynccontextmanager
from fastapi import FastAPI
from model.model import chatrequest, chatresponse
from agent.graph import chatagent
from langchain_core.messages import HumanMessage
from decouple import config 
from langgraph.checkpoint.redis import AsyncRedisSaver
from database.database import engine
from database.database import Base
from sqlalchemy.orm import Session
from fastapi import Depends
from database.database import get_db
from database.crud import save_conversation
from database.crud import get_conversation_by_session
from database.crud import count_completed_bookings
from model.model import ConversationResponse
from typing import List


Base.metadata.create_all(bind=engine)
saver_context=None
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    redis_url = config("REDIS_URL")

    saver_context = AsyncRedisSaver.from_conn_string(redis_url)

    async with saver_context as checkpointer:
        await checkpointer.setup()
    
        agent = chatagent(checkpointer=checkpointer)
        app.state.graph = agent.get_compiled_graph()
        print("redis set-up complete")

        yield

app = FastAPI(title="clinic slot booking agent",lifespan=lifespan)


@app.post("/chat", response_model=chatresponse)

async def chat_endpoint(request: chatrequest,db:Session=Depends(get_db)) -> chatresponse:
    graph=app.state.graph
    completed_bookings = count_completed_bookings(db, request.session_id)
    thread_id = f"{request.session_id.lower()}:booking:{completed_bookings}"
    graph_config = {"configurable": {"thread_id": thread_id}}
    state = {"messages": [HumanMessage(content=request.user_message)]}
    
   
    result = await graph.ainvoke(state, config=graph_config)
    
    ai_message = result["messages"][-1].content
 
    save_conversation(
        db=db,
        session_id=request.session_id,
        human_message=request.user_message,
        ai_message=ai_message,
    )
    
    return chatresponse(
        session_id=request.session_id,
        user_message=ai_message,
    )


@app.get("/conversations/{session_id}", response_model=List[ConversationResponse])

def get_conversation_by_session_id(
    session_id: str,
    db: Session = Depends(get_db),):
    conversation = get_conversation_by_session(db, session_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="No conversation found for this session_id")
    return [
        ConversationResponse(
            id=chat.id,
            session_id=chat.session_id,
            human_message=chat.Human_message,
            ai_message=chat.AI_message,
            created_at=chat.created_at,
        )
        for chat in conversation
    ]
    
