from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
import json
from flask_jsglue import JSGlue

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'survey_database'
app.config["MONGO_URI"] = "mongodb://localhost:27017/survey_database"
mongo = PyMongo(app)
jsglue = JSGlue(app)
@app.route('/', methods=['POST', 'GET'])
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return "Your are logged in "

@app.route('/login', methods=['POST'])
def login():
    error = None
    if request.method == 'POST':
        users = mongo.db.user_db
        login_user = users.find_one({'email': request.form['email']})
        if login_user:
            if bcrypt.checkpw(request.form['psw'].encode('utf-8'), login_user['password']) :
                session['email'] = request.form['email']
                return redirect(url_for('select_criteria'))
            else :
                error = 'Invalid email/password combination'
        else:
            error = 'Invalid email'
    else: return render_template('index.html', error = error)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.user_db
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['psw'].encode('utf-8'), bcrypt.gensalt())
            if request.form['psw'] != request.form['psw-repeat']:
                return 'passwords unmatched'
            users.insert({'email' : request.form['email'], 'name': request.form['name'], 'password' : hashpass,'articles_seen': []})
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register.html')

@app.route('/select_criteria', methods=['POST', 'GET'])
def select_criteria():
    #todo:
    # make the criteria dynamic
    # insert a NA option in the drop down
    article = mongo.db.article_db
    user = mongo.db.user_db
    user_info = user.find_one({'email': session['email']}, {'email': 1, 'name': 1, 'articles_seen': 1})
    #print(user_info)
    articles = list(article for article in article.find())
    language = article.distinct('language')
    publisher = article.distinct('publisher')
    language.append('None')
    publisher.append('None')
    if request.method == 'GET':
        return render_template('criterion.html', language=language, publisher = publisher, not_found= 0)
    elif request.method == 'POST':
        session['parameters'] = []
        for i in request.form:
            if request.form[i] != 'None':
                session['parameters'].append((i, request.form[i]))
        current_article = {}
        for article in articles:
            for i in session['parameters']:
                if i[1] != 'None' and article[i[0]] == i[1]:
                    if not user_info["articles_seen"]:
                        #print("asdf")
                        current_article = article
                    elif article['article_id'] not in user_info["articles_seen"]:
                        #print("qwer")
                        current_article = article
            if current_article is not None:
                break
        #print("cur art", current_article)
        #print("param", session['parameters'])
        if current_article is None:
            return render_template('criterion.html', language=language, publisher=publisher, not_found=1)
        else:
            return redirect(url_for('display_article'))


@app.route('/display_article', methods = ['POST', 'GET'])
def display_article():
    annotation_data = {}
    article_id = ''
    if request.method == 'GET':
        article = mongo.db.article_db
        articles = list(article for article in article.find())
        user = mongo.db.user_db
        user_info = user.find_one({'email': session['email']}, {'email': 1, 'name': 1, 'articles_seen': 1})
        #print(user_info)
        current_article = {}
        #print(session['parameters'])
        for article in articles:
            if session['parameters']:
                bool_condition = list(article[i[0]] == i[1] for i in session['parameters'])
                if False not in bool_condition:
                    if not user_info["articles_seen"]:
                        #print("asdf")
                        current_article = article
                        user.update_one({'email': session['email']},
                                        {'$set': {"articles_seen": [article['article_id']]}})
                    elif article['article_id'] not in user_info["articles_seen"]:

                        #print('qwer', article['article_id'])
                        current_article = article
                        #print(user_info["articles_seen"])
                        user_info['articles_seen'].append(article['article_id'])
                        #print(user_info["articles_seen"])
                        user.update_one({'email': session['email']},
                                        {'$set': {"articles_seen": user_info['articles_seen']}})
                    else:
                        #print("zxcv")
                        continue
            else:
                if not user_info["articles_seen"]:
                    current_article = article
                    user.update_one({'email': session['email']},
                                    {'$set': {"articles_seen": [article['article_id']]}})
                elif article['article_id'] not in user_info["articles_seen"]:

                    #print('qwer', article['article_id'])
                    current_article = article
                    #print(user_info["articles_seen"])
                    user_info['articles_seen'].append(article['article_id'])
                    #print(user_info["articles_seen"])
                    user.update_one({'email': session['email']},
                                    {'$set': {"articles_seen": user_info['articles_seen']}})
                else:
                    #print("zxcv")
                    continue
            #print(current_article)
            if current_article != {}:
                break
        if current_article == {}:
            return redirect(url_for("select_criteria"))
        session['article_id'] = current_article['article_id']
        with open('article_'+current_article['article_id']+'.json') as f:
            annotation_data = json.load(f)
            annotation_data = json.dumps(annotation_data)
        session['annotation_data'] = annotation_data
        user_info = user.find_one({'email': session['email']}, {'email': 1, 'name': 1, 'articles_seen': 1})
        return render_template('display_article.html', annotation_data_json=annotation_data, form_data='not yet')

    if request.method == 'POST':
        feedback = mongo.db.user_feedback

        form_feedback = request.form.get('submit', None)
        print(form_feedback)
        x = feedback.insert_one({'user_email' : session['email'], 'article_id': session['article_id'], 'feedback': form_feedback})
        return redirect(url_for('display_article'))

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True, port=7000)