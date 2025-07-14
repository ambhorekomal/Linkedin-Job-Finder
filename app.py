
from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HUGGINGFACE_API_KEY = "your_api_key_here"
SERPAPI_KEY = "your_api_key_here"

def get_links(keyword, location, num_results=10):
    query = f"{keyword} {location} site:linkedin.com/jobs"
    url = f"https://serpapi.com/search.json?q={query}&api_key={SERPAPI_KEY}&num={num_results}"
    response = requests.get(url)
    data = response.json()
    return [item["link"] for item in data.get("organic_results", []) if "link" in item]

def get_description(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p"))
        return text[:3000] if text else "No description found."
    except:
        return "Failed to fetch description."

def summarize(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": text[:2000]}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            summary = response.json()[0]['summary_text']
            return summary
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        keyword = request.form["keyword"]
        location = request.form["location"]
        links = get_links(keyword, location)
        results = []
        for link in links:
            desc = get_description(link)
            summary = summarize(desc) if desc else "Could not extract description."
            results.append({"link": link, "summary": summary})
        return render_template("results.html", results=results, keyword=keyword, location=location)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
