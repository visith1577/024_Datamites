from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from workflow_init import main, rag_main
from pydantic import BaseModel, Field
from enum import Enum
import streamlit as st
import json

from dotenv import load_dotenv
import asyncio
import os
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


class AcceptBool(str, Enum):
    true = "true"
    false = "false"

class Query(BaseModel):
    requery: str = Field(description="The query to be processed")
    accept: AcceptBool = Field(description="Accept the query or not")
    is_requery: AcceptBool = Field(description="Is this a requery or not")
    toxic: AcceptBool = Field(default=AcceptBool.true, description="Is the query toxic or not")



st.set_page_config(
    page_title="Political Analyst", 
    page_icon="🧊", 
    layout="wide"
)

st.title("Political Analyst")

with st.expander("Settings"):
    rag_only = st.checkbox("Use RAG model only")
    func_only = st.checkbox("Use Web search only")

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Hello how may i assist you?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):

        llm_route = OpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            ChatMessage(role="system", content=
            """You are an assistant that acts an Guardrail to a political Analyst chatbot. 
            Your task is to: 
            * identify if the query is too sensitive or not. If the query is too sensitive, you should provide a response that is not too sensitive and return is_requery = true, else leave it as it is and return requery = false.
            * Identify if the query is relavent to Srilankan politics, if not return accept = false, else return true.
            * If query contains toxic content, gibberish or explicit content, accept = false, toxic = true.
            """),
            ChatMessage(role="user", content=prompt),
        ]

        query_str = llm_route.as_structured_llm(Query).chat(messages=messages).message.content

        query_obj = json.loads(query_str)

        if query_obj["is_requery"] == "true":
            prompt = query_obj["requery"]

        if query_obj["accept"] == "true":
            if rag_only and not func_only:
                response = asyncio.run(rag_main(query=prompt))
            elif func_only and not rag_only:
                response = asyncio.run(main(query=prompt))
            else:
                response1 = asyncio.run(rag_main(query=prompt))
                response = asyncio.run(main(query=f"I will provide you with infomation to supplement the query. break down the facts and individually research about them and provide a formulated final answer to the query. {prompt}. INFOMATION: {response1}"))
        else:
            response = "I am sorry i am unable to assist you with that query."
            st.warning("Content filter detected toxic content in the query. Please rephrase the query and try again.")

        st.markdown(response)
    
        st.session_state.messages.append({"role": "assistant", "content": response})