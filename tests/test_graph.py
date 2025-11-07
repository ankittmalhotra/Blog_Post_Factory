from blog_post_factory.graph import graph_app

def test_graph():
    topic = "re-keying locks"
    inputs = {"topic": topic}
    graph_app.invoke(inputs)
