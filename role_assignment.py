from nltk.corpus import wordnet as wn
from entity_recognition import get_top_entities, extract_article
# pip3 install textblob
from textblob import TextBlob

# pip3 install news-please
# pip3 install newspaper3k
from newsplease import NewsPlease
from newspaper import Article
# pip install beautifulsoup4
# pip install lxml
# pip install html5lib
from bs4 import BeautifulSoup

HERO_DICT = ["brave", "strong"]
VILLAIN_DICT = ["bad"]
VICTIM_DICT = ["kidnapped"]


def word_similarity(word_1, word_2):
    '''
    Returns the Wu-Palmer similarity between the given words.
    Values range between 0 (least similar) and 1 (most similar).
    '''
    try:
        a = wn.synsets(word_1)[0]
        b = wn.synsets(word_2)[0]
        return a.wup_similarity(b)
    except IndexError:
        return 0


def extract_by_newspaper(url):
    content = Article(url)
    content.download()
    content.parse()
    headline = content.title
    article = content.text
    return headline, article


def extract_by_newsplease(url):
    content = NewsPlease.from_url(url)
    headline = content.title
    article = content.text
    return headline, article


def extract_by_soup(url):
    content = BeautifulSoup(url, "lxml")
    headline = content.title.string
    articleList = list()
    for i in content.find_all("p"):
        articleList.append(i.get_text())
        # print(i.get_text())

    return headline, articleList  # TODO modify output so article is string


def decay_function(decay_factor, entity_location, term_index):
    distance = abs(term_index - entity_location[0])
    if len(entity_location) > 1:
        distance = min(distance, abs(term_index - entity_location[1]))
    return (1 - decay_factor) ** distance


def sentiment(word):
    '''
    Returns the sentiment of the given string as a float within
    the range [-1.0, 1.0]
    '''
    word_blob = TextBlob(word)
    return word_blob.sentiment.polarity


def choose_role(word):
    '''
    Uses the sentiment score of a term to determine which dictionary is likely
    to be most useful.
    '''
    s = sentiment(word)
    if s > 0:
        return "hero"
    elif s < 0:
        return "villain"
    else:
        return "all"


def similarity_to_role(word, role):
    similarity_total = 0
    if role == "hero":
        dict_length = len(HERO_DICT)
        for hero_term in HERO_DICT:
            similarity_total += word_similarity(word, hero_term) / dict_length
    elif role == "villain":
        dict_length = len(VILLAIN_DICT)
        for villain_term in VILLAIN_DICT:
            similarity_total += word_similarity(word, villain_term) / dict_length
    elif role == "victim":
        dict_length = len(VICTIM_DICT)
        for victim_term in VICTIM_DICT:
            similarity_total += word_similarity(word, victim_term) / dict_length
    return similarity_total  # TODO I(Quinn) added this to avoid an error (there was not return before), not sure if correct return val


def role_score_by_sentence(entity, role, index, entity_location, article):
    '''
    Calculates the role score of the entity in the given sentence.
    entity_location is a list where the elements are the beginning and ending indices
    '''
    total_score = 0
    article = extract_article(article)
    sentence = article[index]
    begin_index = entity_location[0]
    end_index = entity_location[1] if len(entity_location) > 1 else entity_location[0]
    for i in range(len(sentence)):
        cur_score = 0
        if not begin_index <= i <= end_index:
            cur_score += similarity_to_role(sentence[i], role)
            # cur_score += additional_score(entity, role, sentence[i])
            cur_score *= decay_function(0.5, entity_location, i)
        total_score += cur_score
    return total_score


def entity_role_score(entity, role, article):
    '''
    Calculates the role score of the entity by averaging the
    role scores of the sentences where the entity appears.
    '''
    sentences = entity.locations
    total_score = 0
    count = 0
    for index in sentences:
        total_score += role_score_by_sentence(entity, role, index, sentences[index], article)
        count += 1
    print(total_score)
    return total_score / count


def main(url):
    '''
    Retrieve the three top entities from entity_recognition.py;
    assign each entity a role
    '''
    headline, article = extract_by_newsplease(url)
    entities = get_top_entities(headline, article)
    for entity in entities:
        role = "hero"
        score = entity_role_score(entity, "hero", article)
        cur = entity_role_score(entity, "villain", article)
        if cur > score:
            score = cur
            role = "villain"
        if entity_role_score(entity, "victim", article) > score:
            role = "victim"
        entity.role = role
        print(entity.role)
    return entities


if __name__ == "__main__":
    main("https://www.npr.org/2019/01/13/684645947/los-angeles-teachers-are-moving-forward-with-a-strike")
