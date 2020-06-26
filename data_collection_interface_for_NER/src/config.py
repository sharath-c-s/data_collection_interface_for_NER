import pymongo
import spacy


# mongo import command to create the databases
# os.system('mongoimport --type csv -d survey_database -c article_db --headerline --drop article.csv')


client = pymongo.MongoClient("mongodb://localhost:27017/survey_database")
db = client["survey_database"]
# connecting to the database
article = db["article_db"]

# function to create annotation using spacy
def try_spacy(headline, full_text):
    span_dict = [{"headline": headline, "features": {}}, {"full_text": full_text, "features": {}}]
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(full_text)
    entities = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
    print(entities)
    for i in entities:
        if i[0] not in span_dict[1]['features']:
            span_dict[1]["features"][i[0]] = {"span": [(i[1], i[2])], "entity_type": i[3]}
        else:
            span_dict[1]["features"][i[0]]['span'].append((i[1], i[2]))

    doc = nlp(headline)
    entities = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
    print(entities)
    for i in entities:
        if i[0] not in span_dict[0]['features']:
            span_dict[0]["features"][i[0]] = {"span": [(i[1], i[2])], "entity_type": i[3]}
        else:
            span_dict[0]["features"][i[0]]['span'].append((i[1], i[2]))

    return span_dict

articles = list(article for article in article.find())

# for each of the article, creating the annotation data
for i in range(len(articles)):
    # to take care of any special undefinable characters in the text
    my_str_as_bytes = str.encode(articles[i]["full_text"])
    articles[i]["full_text"] = my_str_as_bytes.decode('utf-8', errors='replace').replace('\uFFFD', '\'')
    articles[i]["full_text"] = articles[i]["full_text"].replace("\n\n", " ")
    article.update_one({'article_id': articles[i]["full_text"]}, {"$set": {'full_text': articles[i]["full_text"]}})
    print(articles[i]["full_text"])
    # calling the function
    span_dict = try_spacy(articles[i]["headline"],articles[i]["full_text"])
    # add annotation data to database
    article.update_one({'article_id': articles[i]['article_id']},{'$set': {'article_annotation': span_dict}})




