import os, json
import fitz
from llama_index.core import (
    Document,
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.tools import (
    QueryEngineTool,
    ToolMetadata
)
from llama_index.core.workflow import (
    step,
    Context,
    Workflow,
    StartEvent,
    StopEvent
)

from event import QueryEvent, AnswerEvent

from llama_index.core.agent import ReActAgent
from dotenv import load_dotenv 

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


class SubQuestionQueryEngine(Workflow):

    @step(pass_context=True)
    async def query(self, ctx: Context, ev: StartEvent) -> QueryEvent:
        if (hasattr(ev, "query")):
            ctx.data["original_query"] = ev.query
            print(f"Query is {ctx.data['original_query']}")

        if (hasattr(ev, "llm")):
            ctx.data["llm"] = ev.llm

        if (hasattr(ev, "tools")):
            ctx.data["tools"] = ev.tools

        response = ctx.data["llm"].complete(f"""
            Given a user question, and a list of tools, output a list of
            relevant sub-questions, such that the answers to all the
            sub-questions put together will answer the question. Respond
            You will be asked questions about the politics in Srilanka.
            extra info: 
            political parties : UNP, SJB and NPP
            in pure JSON without any markdown, like this:
            {{
                "sub_questions": [
                    "What is the current state of poilitics in Srilanaka?",
                    "Who is most likely to win the presedential race in srilanka?",
                    "What are claims made by the current president of srilanka?"
                ]
            }}
            Here is the user question: {ctx.data['original_query']}

            And here is the list of tools: {ctx.data['tools']}
            """)

        print(f"Sub-questions are {response}")

        response_obj = json.loads(str(response))
        sub_questions = response_obj["sub_questions"]

        ctx.data["sub_question_count"] = len(sub_questions)

        for question in sub_questions:
            self.send_event(QueryEvent(question=question))

        return None

    @step(pass_context=True)
    async def sub_question(self, ctx: Context, ev: QueryEvent) -> AnswerEvent:
        print(f"Sub-question is {ev.question}")

        agent = ReActAgent.from_tools(ctx.data["tools"], llm=ctx.data["llm"], verbose=True)
        response = agent.chat(ev.question)

        return AnswerEvent(question=ev.question,answer=str(response))

    @step(pass_context=True)
    async def combine_answers(self, ctx: Context, ev: AnswerEvent) -> StopEvent | None:
        ready = ctx.collect_events(ev, [AnswerEvent]*ctx.data["sub_question_count"])
        if ready is None:
            return None

        answers = "\n\n".join([f"Question: {event.question}: \n Answer: {event.answer}" for event in ready])

        prompt = f"""
            You are given an overall question that has been split into sub-questions,
            each of which has been answered. Combine the answers to all the sub-questions
            into a single answer to the original question.

            Original question: {ctx.data['original_query']}

            Sub-questions and answers:
            {answers}
        """

        print(f"Final prompt is {prompt}")

        response = ctx.data["llm"].complete(prompt)

        print("Final response is", response)

        return StopEvent(result=str(response))
    

def extract_text_from_pdf(pdf_path: str):
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

class CustomDirectoryReader(SimpleDirectoryReader):
    def load_data(self):
        documents = []
        for file in self.input_files:
            if file.name.endswith(".pdf"):
                text = extract_text_from_pdf(file)
                doc = Document(text=text, metadata={"filename": os.path.basename(file)})
                documents.append(doc)
            else:
                with open(file, "r") as f:
                    text = f.read()
                    doc = Document(text=text, metadata={"filename": os.path.basename(file)})
                    documents.append(doc)
        return documents


def prepare_query_engine(documents_folder: str):
    # documents folder contains sub directories with text files
    # name of sub directory is the metadata discription
    query_engine_tools = []


    for subdir in os.listdir(documents_folder):
        subdir_path = os.path.join(documents_folder, subdir)
        if os.path.isdir(subdir_path):
            index_persist_path = f"./storage/{subdir}/"

            if os.path.exists(index_persist_path):
                storage_context = StorageContext.from_defaults(persist_dir=index_persist_path)
                index = load_index_from_storage(storage_context)
            else:
                input_files = [os.path.join(subdir_path, file) for file in os.listdir(subdir_path)]
                documents = CustomDirectoryReader(input_files=input_files).load_data()
                index = VectorStoreIndex.from_documents(documents)
                index.storage_context.persist(index_persist_path)

            engine = index.as_query_engine()
            query_engine_tools.append(
                QueryEngineTool(
                    query_engine=engine,
                    metadata=ToolMetadata(
                        name=subdir,
                        description=f"Information about {subdir}",
                    ),
                )
            )

    return query_engine_tools