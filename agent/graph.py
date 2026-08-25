from openai.types import eval_stored_completions_data_source_config
from model.model import GraphState
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
#from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver  
#from redis import Redis
from langchain_groq import ChatGroq 
from config import *
from prompt.prompt import get_system_prompt
from tool.book_slot import create_slot
from tool.check_availability import check_availability
from typing import Literal

class chatagent:
    def __init__(self,checkpointer):

        self.checkpointer=checkpointer
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL_NAME,
            temperature=0.4,
        )

        self.tool = [check_availability, create_slot]
        self.llm_bind = self.llm.bind_tools(self.tool)
    
#AGENT NODE

    async def agent_node(self, state: GraphState):
        try:
            prompt = [SystemMessage(content=get_system_prompt())] + state["messages"]
            response = await self.llm_bind.ainvoke(prompt)
            return {"messages": [response]}
        except Exception as e:
            return {"messages": [SystemMessage(content=f"Error: {str(e)}")]}

#TOOL NODE

    def tools_condition(self, state: GraphState) -> Literal["tools", "__end__"]:
        messages = state.get("messages", [])
        if messages and getattr(messages[-1], "tool_calls", None):
            return "tools"
        return "__end__"

#GRAPH COMPILE

    def get_compiled_graph(self):
        nodes = ToolNode(self.tool)
        graph = StateGraph(GraphState)

        graph.add_node("agent", self.agent_node)
        graph.add_node("tools", nodes)
        
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", self.tools_condition)
        graph.add_edge("tools", "agent")
        
        return graph.compile(checkpointer=self.checkpointer)


    