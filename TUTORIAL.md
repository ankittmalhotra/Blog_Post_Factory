# Blog Post Factory Tutorial

This tutorial will guide you through the process of using the Blog Post Factory to generate a blog post.

## Prerequisites

Before you begin, make sure you have followed the installation instructions in the `README.md` file. You should have the following running:

*   The Ollama server with the `gemma3:4b` model.
*   The Blog Post Factory application (`python app.py`).

## Step 1: Open the Application

Open your web browser and navigate to `http://localhost:8001`. You should see the Blog Post Factory interface.

## Step 2: Enter a Topic

Enter the topic for your blog post in the text area. For example, you could enter "The benefits of a standing desk".

## Step 3: Generate the Blog Post

Click the "Generate Blog Post" button. The application will start generating the blog post. You will see the status of the generation process in real-time.

## Step 4: View the Blog Post

As the blog post is being generated, it will be displayed in the "Blog Post Output" section. The final, polished blog post will be displayed once the generation process is complete.

## Step 5: Review the Output

The generated blog post is saved in the `reviews` directory. The filename is a sanitized version of the topic you entered. For example, if you entered "The benefits of a standing desk", the file will be saved as `The_benefits_of_a_standing_desk_review.txt`.

You can open this file to see the final version of the blog post.

## Conclusion

You have successfully generated a blog post using the Blog Post Factory. You can now use this process to generate blog posts on any topic you want.
