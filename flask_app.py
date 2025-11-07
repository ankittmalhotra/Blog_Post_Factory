import os
import logging
from flask import Flask, render_template, request
from blog_post_factory.graph import app as blog_post_app

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    logging.info("Serving index.html")
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    topic = request.form['topic']
    logging.info(f"Received topic: {topic}")
    inputs = {"topic": topic}
    post = ""
    for event in blog_post_app.stream(inputs):
        if "post" in event:
            post = event["post"]
    logging.info(f"Generated post: {post}")

    # Save the post to an HTML file
    if not os.path.exists('posts'):
        os.makedirs('posts')
    with open(f"posts/{topic}.html", "w") as f:
        f.write(post)

    return post

if __name__ == '__main__':
    app.run(debug=True)
