import logging
import os
from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global variable for the LLM
llm = None

def get_llm():
    global llm
    if llm is None:
        llm = ChatOllama(model="gemma3:4b", base_url="http://localhost:11434")
    return llm

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
    summarized_research: str
    post: str


def planner(state: State):
    logging.info("Planning the blog post...")
    yield {"status": "Planning...", "current_step": "Generating blog post plan"}
    prompt = f"""Create a detailed, SEO-friendly blog post plan for the topic: {state['topic']}.

    Your plan should include:
    1.  An introduction that hooks the reader.
    2.  A few main sections that are informative and easy to read.
    3.  A conclusion that summarizes the main points and includes a call to action.

    Please provide the plan as a numbered list."""
    plan_str = get_llm().invoke(prompt).content
    plan = [item for item in plan_str.split("\n") if item.strip()]    
    logging.info(f"Generated plan: {plan}")
    yield {"plan": plan, "status": "Planning complete"}


def researcher(state: State):
    logging.info("Researching the blog post...")
    yield {"status": "Researching...", "current_step": "Starting research"}
    research_results = []
    for i, step in enumerate(state["plan"]):
        logging.info(f"Researching step: {step}")
        yield {"status": "Researching...", "current_step": f"Researching step {i+1}/{len(state['plan'])}: {step}"}
        
        # Use the search tool to get raw search results
        raw_search_output = search.run(step)
        research_results.append(raw_search_output)
        yield {"status": "Researching...", "current_step": f"Completed search for step {i+1}/{len(state['plan'])}"}

    logging.info(f"Generated research: {research_results}")
    yield {"research": research_results, "status": "Research complete"}


def _summarize_chunk(chunk: str, topic: str) -> str:
    """Summarizes a single chunk of research."""
    prompt = f"""Given the following research chunk for a blog post on {topic}, provide a very concise summary of this chunk.
    Focus on key information relevant to the topic.

    Research Chunk:
    {chunk}"""
    return get_llm().invoke(prompt).content

MAX_CHUNK_LENGTH = 2000  # Approximately 500 tokens for gemma3:4b

def research_summarizer(state: State):
    logging.info("Summarizing research in chunks...")
    yield {"status": "Summarizing research", "current_step": "Starting research summarization"}
    all_research_summaries = []
    for i, research_item in enumerate(state["research"]):
        logging.info(f"Summarizing research item {i+1}/{len(state['research'])}...")
        yield {"status": "Summarizing research", "current_step": f"Summarizing research item {i+1}/{len(state['research'])}"}
        
        current_item_summaries = []
        if len(research_item) > MAX_CHUNK_LENGTH:
            logging.info(f"Research item {i+1} is too large, chunking...")
            yield {"status": "Summarizing research", "current_step": f"Chunking and summarizing large research item {i+1}"}
            # Split into smaller chunks
            for j in range(0, len(research_item), MAX_CHUNK_LENGTH):
                sub_chunk = research_item[j:j + MAX_CHUNK_LENGTH]
                sub_chunk_summary = _summarize_chunk(sub_chunk, state["topic"])
                current_item_summaries.append(sub_chunk_summary)
            chunk_summary = " ".join(current_item_summaries) # Combine sub-chunk summaries
        else:
            chunk_summary = _summarize_chunk(research_item, state["topic"])
            
        all_research_summaries.append(chunk_summary)
    
    combined_summaries = "\n".join(all_research_summaries)
    
    logging.info("Generating final summary from chunk summaries...")
    yield {"status": "Summarizing research", "current_step": "Generating final summary from chunk summaries"}
    # If combined_summaries is still too large, we might need another layer of summarization here.
    # For now, we'll assume the chunking of individual research items is sufficient.
    prompt = f"""Given these concise summaries of research chunks for a blog post on {state['topic']},
    provide a single, very concise summary of all the research. This final summary will be used to write the blog post,
    so ensure it captures all key points without unnecessary detail.

    Chunk Summaries:
    {combined_summaries}"""
    summarized_research = get_llm().invoke(prompt).content
    logging.info(f"Generated final summarized research: {summarized_research}")
    yield {"summarized_research": summarized_research, "status": "Research summarization complete"}


def writer(state: State):
    logging.info("Writing the blog post...")
    yield {"status": "Writing", "current_step": "Generating blog post content"}
    prompt = f"""Write a full blog post based on the following plan and summarized research.

    Topic: {state['topic']}

    Plan:
    {state['plan']}

    Summarized Research:
    {state['summarized_research']}

    The blog post should have a catchy title, be well-structured, and include a call to action at the end. Ensure the output is a complete blog post with a title, introduction, body, and conclusion."""
    post = get_llm().invoke(prompt).content
    logging.info(f"Generated post: {post}")
    yield {"post": post, "status": "Writing complete"}

def reviewer(state:State):
    logging.info("Reviewing the blog post...")
    yield {"status": "Reviewing", "current_step": "Starting review of blog post"}
    prompt = f"""Proofread and polish the following blog post to make it publication-ready.
    Correct any grammatical errors, improve clarity, and ensure a professional tone suitable for a live website.
    Do not add any introductory or concluding remarks, questions, or your own opinions. Only output the final, polished blog post text.

    Blog Post:
    {state['post']}"""
    review_feedback = get_llm().invoke(prompt).content
    logging.info(f"Review feedback: {review_feedback}")

    # Define the output directory for reviews
    output_dir = "reviews"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sanitize the topic to create a valid filename
    sanitized_topic = "".join(c for c in state['topic'] if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
    file_path = os.path.join(output_dir, f"{sanitized_topic}_review.txt")

    with open(file_path, "w") as f:
        f.write(review_feedback)
    logging.info(f"Review feedback saved to {file_path}")
    yield {"status": "Review complete"}
# Graph
workflow = StateGraph(State)
workflow.add_node("planner", planner)
workflow.add_node("researcher", researcher)
workflow.add_node("research_summarizer", research_summarizer)
workflow.add_node("writer", writer)
workflow.add_node("reviewer", reviewer)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "research_summarizer")
workflow.add_edge("research_summarizer", "writer")
workflow.add_edge("writer", "reviewer")
workflow.add_edge("reviewer", END)
 
graph_app = workflow.compile()

if __name__ == "__main__":
    topic = "re-keying locks"
    inputs = {"topic": topic}
    for event in graph_app.stream(inputs):
        print(event)
