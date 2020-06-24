import pymongo
import json
import spacy
import re

#to create the databases
# os.system('mongoimport --type csv -d survey_database -c article_db --headerline --drop article.csv')
# os.system('mongoimport --type csv -d survey_database -c noun_db --headerline --drop noun.csv')
# os.system('mongoimport --type csv -d survey_database -c location_db --headerline --drop location.csv')



client = pymongo.MongoClient("mongodb://localhost:27017/survey_database")
db = client["survey_database"]
nouns = db["noun_db"]
locations = db["location_db"]
article = db["article_db"]
def get_json(headline, full_text, nouns, locations):
    sp = spacy.load('en_core_web_sm')
    sen1 = sp(full_text)
    sen2 = sp(headline)
    # print(sen.text)
    # print([token.text for token in sen])
    span_dict = [{"headline": headline, "features": {}}, {"full_text": full_text, "features": {}}]
    for token in sen2:
        if True in list(str(token).casefold() == loc['city'].casefold() for loc in locations):
            # print(token, token.idx, token.idx + len(str(token)))
            if str(token) not in span_dict[0]['features']:
                span_dict[0]["features"][str(token)] = {"span" : [[token.idx, token.idx + len(str(token))]], "entity_type" : "location"}
            else:
                span_dict[0]["features"][str(token)]['span'].append((token.idx, token.idx + len(str(token))))
        elif True in list(str(token).casefold() == noun['noun'].casefold() for noun in nouns):
            # print(token, token.idx, token.idx + len(str(token)))
            if str(token) not in span_dict[0]['features']:
                span_dict[0]["features"][str(token)] = {"span" : [[token.idx, token.idx + len(str(token))]], "entity_type" : "name"}
            else:
                span_dict[0]["features"][str(token)]['span'].append((token.idx, token.idx + len(str(token))))

    for token in sen1:
        if True in list(str(token).casefold() == loc['city'].casefold() for loc in locations):
            # print(token, token.idx, token.idx + len(str(token)))
            if str(token) not in span_dict[1]['features']:
                span_dict[1]["features"][str(token)] = {"span" : [[token.idx, token.idx + len(str(token))]], "entity_type" : "location"}
            else:
                span_dict[1]["features"][str(token)]['span'].append((token.idx, token.idx + len(str(token))))
        elif True in list(str(token).casefold() == noun['noun'].casefold() for noun in nouns):
            # print(token, token.idx, token.idx + len(str(token)))
            if str(token) not in span_dict[1]['features']:
                span_dict[1]["features"][str(token)] = {"span" : [[token.idx, token.idx + len(str(token))]], "entity_type" : "name"}
            else:
                span_dict[1]["features"][str(token)]['span'].append((token.idx, token.idx + len(str(token))))
    print(span_dict)
    return span_dict

articles = list(article for article in article.find())
nouns = list(noun for noun in nouns.find())
locations = list(location for location in locations.find())

#todo
def get_json_re(headline, full_text, nouns, locations):
    span_dict = [{"headline": headline, "features": {}}, {"full_text": full_text, "features": {}}]
    for loc in locations:
        loc_st_end = ([[ind.start(), ind.end()] for ind in re.finditer(loc['city'], full_text)])
        if(len(loc_st_end) > 0):
            if loc['city'] not in span_dict[1]['features']:
                span_dict[1]["features"][loc['city']] = {"span" : loc_st_end, "entity_type" : "location"}
        print(loc_st_end)

        loc_st_end = ([[ind.start(), ind.end()] for ind in re.finditer(loc['city'], headline)])
        if (len(loc_st_end) > 0):
            if loc['city'] not in span_dict[0]['features']:
                span_dict[0]["features"][loc['city']] = {"span": loc_st_end, "entity_type": "location"}
        print(loc_st_end)


    for noun in nouns:
        noun_st_end = ([[ind.start(), ind.end()] for ind in re.finditer(noun['noun'], full_text)])
        if len(noun_st_end) > 0:
            if noun['noun'] not in span_dict[1]['features']:
                span_dict[1]["features"][noun['noun']] = {"span": noun_st_end, "entity_type": noun['noun_type']}
        print(noun_st_end)

        noun_st_end = ([[ind.start(), ind.end()] for ind in re.finditer(noun['noun'], headline)])
        if len(noun_st_end) > 0:
            if noun['noun'] not in span_dict[0]['features']:
                span_dict[0]["features"][noun['noun']] = {"span": noun_st_end, "entity_type": noun['noun_type']}
        print(noun_st_end)
    return span_dict

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


for i in range(len(articles)):
    # span_dict = get_json(articles[i]["headline"],articles[i]["full_text"] , nouns, locations)
    # span_dict = get_json_re(articles[i]["headline"],articles[i]["full_text"] , nouns, locations)
    # to take care of any special undefinable characters in the text
    # my_str_as_bytes = str.encode(articles[i]["full_text"])
    # articles[i]["full_text"] = my_str_as_bytes.decode('utf-8', errors='replace').replace('\uFFFD', '\'')
    # articles[i]["full_text"] = articles[i]["full_text"].replace("\n\n", " ")
    # article.update_one({'article_id': articles[i]["full_text"]}, {"$set": {'full_text': articles[i]["full_text"]}})
    # print(articles[i]["full_text"])
    span_dict = try_spacy(articles[i]["headline"],articles[i]["full_text"])
    with open('F:\\everything_jio\\login_page_for_recomsys\\src\\article_'+ articles[i]['article_id'] +'.json', 'w') as file:
        json_string = json.dumps(span_dict, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        file.write(json_string)




#to take care of any special undefinable characters in the text
# my_str_as_bytes = str.encode(current_article["full_text"])
# current_article["full_text"] = my_str_as_bytes.decode('utf-8', errors='replace').replace('\uFFFD', '\'')
# current_article['full_text'] = current_article['full_text'].replace("\n\n", " ")
# article.update_one({'article_id': current_article["article_id"]}, {"$set": {'full_text': current_article["full_text"]}})
# print(current_article["full_text"])