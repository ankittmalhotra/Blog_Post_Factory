from langchain_core.tools import tool
from langchain_experimental.utilities import DuckDuckGoSearchAPIWrapper
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama

# Initialize the Ollama model
llm = ChatOllama(model="gemma3:4b", base_url="http://localhost:11434")

@tool
def search(query: str):
    """Search for information on DuckDuckGo."""
    search = DuckDuckGoSearchAPIWrapper()
    return search.run(query)


# State
class State(
    TypedDict,
):  # The user can add fields to this class to share information between nodes
    # The user can also add fields to this class to persist information between runs of the graph
    topic: str
    plan: list[str]
    research: list[str]
    post: str


def planner(state: State):
    prompt = f"""Create a detailed, SEO-friendly blog post plan for the topic: {state['topic']}.

    Your plan should include:
    1.  An introduction that hooks the reader.
    2.  A few main sections that are informative and easy to read.
    3.  A conclusion that summarizes the main points and includes a call to action.

    Please provide the plan as a numbered list."""
    plan_str = llm.invoke(prompt).content
    plan = [item for item in plan_str.split("\n") if item.strip()]    
    return {"plan": plan}


def researcher(state: State):
    research = []
    for step in state["plan"]:
        prompt = f"""Research the following step for a blog post on {state['topic']}: {step}

        Please provide a concise summary of the research."""
        research.append(llm.invoke(prompt).content)
    return {"research": research}


def writer(state: State):
    prompt = f"""Write a full blog post based on the following plan and research.

    Topic: {state['topic']}

    Plan:
    {state['plan']}

    Research:
    {state['research']}

    The blog post should have a catchy title, be well-structured, and include a call to action at the end."""
    post = llm.invoke(prompt).content
    return {"post": post}


# Graph
workflow = StateGraph(State)
workflow.add_node("planner", planner)
workflow.add_node("researcher", researcher)
workflow.add_node("writer", writer)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

if __name__ == "__main__":
    topic = "re-keying locks"
    inputs = {"topic": topic}
    for event in app.stream(inputs):
        print(event)
