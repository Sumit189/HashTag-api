import os
from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
nltk.download('stopwords')
nltk.download('punkt')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

app = Flask(__name__)

def rank_tags(keywords, tags):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform([*keywords, *tags])
    keyword_vectors = X[:len(keywords)]
    tag_vectors = X[len(keywords):]
    similarity_matrix = cosine_similarity(keyword_vectors, tag_vectors)
    ranked_words = {}
    for i, keyword in enumerate(keywords):
        ranked_words[keyword] = {}
        for j, tag in enumerate(tags):
            ranked_words[keyword][tag] = similarity_matrix[i][j]
    return ranked_words

def get_top_tags(ranked_words, threshold, num_tags):
    all_tags = {}
    for keyword in ranked_words:
        for tag, score in ranked_words[keyword].items():
            if tag not in all_tags:
                all_tags[tag] = 0
            all_tags[tag] += score
    top_tags = [tag for tag, score in sorted(all_tags.items(), key=lambda x: x[1], reverse=True) if score >= threshold][:num_tags]
    return top_tags

@app.route('/', methods=['GET'])
def hello():
    return 'Hello from API'

@app.route('/getHashtags', methods=['POST'])
def trending_hashtags():
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        
        data = request.get_json()
        if 'keywords' not in data or 'tags' not in data:
            return jsonify({'error': 'Missing Data'}), 400

        threshold = 0.5
        num_Tags = 30
        if data['threshold']:
            threshold = data['threshold']

        if data['num_Tags']:
            num_Tags = data['num_Tags']
        
        ranked_words = rank_tags(data['keywords'], data['tags'])
        trending_hashtags = get_top_tags(ranked_words, threshold, num_Tags)
        if trending_hashtags:
            trending_hashtags = ['#' + tag for tag in trending_hashtags]
        return jsonify({'trending_hashtags': trending_hashtags}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_keywords', methods=['POST'])
def extract_keywords():
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        
        data = request.get_json()
        if 'text' not in data:
            return jsonify({'error': 'Missing Data'}), 400

        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(data['text'].lower())
        keywords = [token for token in tokens if token not in stop_words and token.isalpha()]
        return keywords
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0')
