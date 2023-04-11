import os
import spacy
import requests
import fake_useragent
import re
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

nlp = spacy.load('en_core_web_sm')

def find_keywords(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop and len(token) > 2]
    return keywords

def get_trending_hashtags(tag, sessionid):
    url = 'https://www.instagram.com/web/search/topsearch/?context=blended&query=' + tag
    try:
        # Generate a random user agent
        user_agent = fake_useragent.UserAgent().random
        headers = {
            'User-Agent': user_agent,
            'Cookie': f'sessionid={sessionid};'
        }

        # Send the request with the random user agent and login cookies
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = json.loads(response.text)
        hashtags = data['hashtags']
        return [hashtag['hashtag']['name'] for hashtag in hashtags]
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while getting hashtags for {tag}: {e}")
        return []

def rank_hashtags(text, hashtags):
    doc = nlp(text)
    hashtag_counts = defaultdict(int)
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop and len(token) > 2:
            for hashtag in hashtags:
                if hashtag.lower() in token.text.lower():
                    hashtag_counts[hashtag] += 1
    sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
    print("hashtags {ht}".format(ht=sorted_hashtags))
    return [hashtag[0] for hashtag in sorted_hashtags][:30]

def get_trending_hashtags_from_text(text, sessionId):
    hashtags_regex = r'#\w+'
    hashtags = set(re.findall(hashtags_regex, text))
    trending_hashtags = []
    for hashtag in hashtags:
        hashtags_result = get_trending_hashtags(hashtag[1:], sessionId)
        trending_hashtags.extend(hashtags_result)
    all_hashtags = list(hashtags) + trending_hashtags
    return rank_hashtags(text, all_hashtags)


@app.route('/', methods=['GET'])
def hello():
    return 'Hello from API'

@app.route('/trendingHashtags', methods=['POST'])
def keywords_and_trending_hashtags():
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        
        data = request.get_json()
        if 'text' not in data or 'sessionId' not in data:
            return jsonify({'error': 'Missing Data'}), 400
        text = data['text']
        trending_hashtags = get_trending_hashtags_from_text(text, data['sessionId'])
        return jsonify({'trending_hashtags': trending_hashtags}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0')
