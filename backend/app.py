from flask import Flask, request, jsonify, render_template
import wikipedia
import wikipediaapi
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


user_agent = "MyWikipediaApp/1.0 (https://example.com; myemail@example.com)"

wiki_api = wikipediaapi.Wikipedia(
    language='en',  # Replace 'en' with your desired language
    user_agent=user_agent
)

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)
# Set up Wikipedia
wikipedia.set_lang("en")


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify([])
    results = wikipedia.search(query)
    return jsonify(results)

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json  # For POST requests, retrieve data from the JSON body
    title = data.get('title')
    if not title:
        return jsonify({'error': 'No title provided'}), 400

    page = wiki_api.page(title)
    if page.exists():
        return jsonify({'summary': page.summary})  # Return only the summary
    return jsonify({'error': 'Page not found'}), 404


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    content = data.get('content')
    question = data.get('question')
    if not content or not question:
        return jsonify({'error': 'Content and question are required'}), 400

    prompt = f"Based on this article:\n\n{content}\n\nAnswer this question: {question}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=150
    )
    res = response.choices[0].message.content
    return jsonify({'answer': res.strip()})


@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.json
    title = data.get('title')

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    page = wiki_api.page(title)
    print("PAGE: ", page)
    if not page.exists():
        return jsonify({'error': 'Page not found'}), 404

    content = page.text

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    prompt = f"DO NOT USE ANY ASTERISKS AND DO NOT ADD ANYTHING OTHER THAN JSON. Generate 5 multiple-choice quiz questions based on this content:\n\n{content}. PRODUCE THE OUTPUT IN JSON in the format of 'question, options, correct answer."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=500
    )
    res = response.choices[0].message.content
    print("RES:", res)
    return jsonify({'quiz': res.strip()})

if __name__ == '__main__':
    app.run(debug=True)
