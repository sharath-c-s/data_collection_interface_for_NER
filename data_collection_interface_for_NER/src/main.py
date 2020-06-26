from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
import json
from flask_jsglue import JSGlue

#configuring flask app
app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'survey_database'
app.config["MONGO_URI"] = "mongodb://localhost:27017/survey_database"
mongo = PyMongo(app)
jsglue = JSGlue(app)
#home page

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

#logging in
@app.route('/login', methods=['POST'])
def login():
    error = None
    if request.method == 'POST':
        users = mongo.db.user_db
        login_user = users.find_one({'email': request.form['email']})
        #authenticating the password
        if login_user:
            if bcrypt.checkpw(request.form['psw'].encode('utf-8'), login_user['password']) :
                session['email'] = request.form['email']
                # session['logged_in'] = True
                return redirect(url_for('select_criteria'))
            else :
                error = 'Invalid email/password combination'
        else:
            error = 'Invalid email'
    else: return render_template('index.html', error = error)

#register page
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.user_db
        existing_user = users.find_one({'email': request.form['email']})
        #saving the user details, if the user is not present before
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['psw'].encode('utf-8'), bcrypt.gensalt())
            if request.form['psw'] != request.form['psw-repeat']:
                return 'passwords unmatched'
            users.insert({'email' : request.form['email'], 'name': request.form['name'], 'password' : hashpass,'articles_seen': []})
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register.html')

#criteria selecting page
@app.route('/select_criteria', methods=['POST', 'GET'])
def select_criteria():
    article = mongo.db.article_db
    user = mongo.db.user_db
    user_info = user.find_one({'email': session['email']}, {'email': 1, 'name': 1, 'articles_seen': 1})

    articles = list(article for article in article.find())
    #this is the place where criteria are shown any other new selecting crtieria can be added here
    language = article.distinct('language')
    publisher = article.distinct('publisher')
    language.append('None')
    publisher.append('None')
    # displaying criteria initially
    if request.method == 'GET':
        return render_template('criterion.html', language=language, publisher = publisher, not_found= 0)
    # bringing out a selected article
    elif request.method == 'POST':
        session['parameters'] = []
        for i in request.form:
            if request.form[i] != 'None':
                session['parameters'].append((i, request.form[i]))
        current_article = {}
        # getting the article using inputs of user
        for article in articles:
            for i in session['parameters']:
                if i[1] != 'None' and article[i[0]] == i[1]:
                    if not user_info["articles_seen"]:
                        current_article = article
                    elif article['article_id'] not in user_info["articles_seen"]:
                        current_article = article
            if current_article is not None:
                break
        if current_article is None:
            return render_template('criterion.html', language=language, publisher=publisher, not_found=1)
        else:
            return redirect(url_for('display_article'))

# displaying the article that fits criteria
@app.route('/display_article', methods = ['POST', 'GET'])
def display_article():
    annotation_data = {}
    article_id = ''
    # sending annotation data into the server
    if request.method == 'GET':
        article = mongo.db.article_db
        articles = list(article for article in article.find())
        user = mongo.db.user_db
        user_info = user.find_one({'email': session['email']}, {'email': 1, 'name': 1, 'articles_seen': 1})
        current_article = {}
        # getting that article and updating articles seen by the user
        for article in articles:
            if session['parameters']:
                bool_condition = list(article[i[0]] == i[1] for i in session['parameters'])
                if False not in bool_condition:
                    if not user_info["articles_seen"]:
                        current_article = article
                        user.update_one({'email': session['email']},
                                        {'$set': {"articles_seen": [article['article_id']]}})
                    elif article['article_id'] not in user_info["articles_seen"]:
                        current_article = article
                        user_info['articles_seen'].append(article['article_id'])
                        user.update_one({'email': session['email']},
                                        {'$set': {"articles_seen": user_info['articles_seen']}})
                    else:
                        continue
            else:
                if not user_info["articles_seen"]:
                    current_article = article
                    user.update_one({'email': session['email']},
                                    {'$set': {"articles_seen": [article['article_id']]}})
                elif article['article_id'] not in user_info["articles_seen"]:
                    current_article = article
                    user_info['articles_seen'].append(article['article_id'])
                    user.update_one({'email': session['email']},
                                    {'$set': {"articles_seen": user_info['articles_seen']}})
                else:
                    continue
            if current_article != {}:
                break
        if current_article == {}:
            return redirect(url_for("select_criteria"))
        #get annotation data for the selected article
        session['article_id'] = current_article['article_id']
        annotation_data = current_article['article_annotation']
        annotation_data = json.dumps(annotation_data, default=lambda o: o.__dict__)
        session['annotation_data'] = annotation_data
        print('annotation_data_\n', annotation_data)
        return render_template('display_article.html', annotation_data_json=annotation_data, form_data='not yet')

    # getting feedback form the client and inserting it into database
    if request.method == 'POST':
        feedback = mongo.db.user_feedback
        form_feedback = request.form.get('submit', None)
        print(form_feedback)
        x = feedback.insert_one({'user_email' : session['email'], 'article_id': session['article_id'], 'feedback': form_feedback})
        return redirect(url_for('display_article'))

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True, port=8000)
