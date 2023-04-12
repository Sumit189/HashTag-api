import spacy
from flask import Flask, request, jsonify

app = Flask(__name__)

nlp = spacy.load('en_core_web_sm')

def rank_words(a, b):
    ranked_words = {}
    for a_word in a:
        scores = []
        for b_word in b:
            score = nlp(a_word).similarity(nlp(b_word))
            scores.append(score)
        ranked_words[a_word] = sorted(list(zip(b, scores)), key=lambda x: x[1], reverse=True)[:30]
    return ranked_words

def get_top_words(ranked_words):
    all_words = []
    for words in ranked_words.values():
        all_words.extend([w[0] for w in words])
    top_words = sorted(set(all_words), key=lambda x: max([w[1] for w in ranked_words.values() if x in [w[0] for w in ranked_words[x]]]), reverse=True)[:30]
    top_words = [word for word in top_words if max([w[1] for w in ranked_words.values() if word in [w[0] for w in ranked_words[word]]]) >= 0.5]
    return top_words


@app.route('/', methods=['GET'])
def hello():
    return 'Hello from API'

@app.route('/getHashtags', methods=['POST'])
def keywords_and_trending_hashtags():
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        
        data = request.get_json()
        if 'keywords' not in data or 'tags' not in data:
            return jsonify({'error': 'Missing Data'}), 400

        ranked_words = rank_words(data['keywords'], data['tags'])
        trending_hashtags = get_top_words(ranked_words)
        return jsonify({'trending_hashtags': trending_hashtags}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract_product_names', methods=['POST'])
def extract_product_names_api():
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        
        data = request.get_json()
        if 'text' not in data:
            return jsonify({'error': 'Missing Data'}), 400

        # extract product names from text using spaCy's NER
        doc = nlp(data['text'])
        product_names = set([ent.text for ent in doc.ents if ent.label_ == "PRODUCT"])

        return jsonify({'product_names': list(product_names)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0')
