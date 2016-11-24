import json
import logging 

import spacy_to_naf
import semeval_classes 
from spacy.en import English
nlp = English()

from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF, DC, DCTERMS
import datetime

def start_logger(log_path):
    '''
    logger is started
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create a file handler
    handler = logging.FileHandler(log_path,
                                  mode="w")
    handler.setLevel(logging.DEBUG)

    # create a logging format
    formatter = logging.Formatter('%(filename)s - %(asctime)s - %(levelname)s - %(name)s  - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)
    
    return logger 

def process_first_x_files(path_signalmedia_json, start=None, end=None):
    """
    create generator of json objects (representing signalmedia articles)
    
    :param str path_signalmedia_json: path to all signalmedia article in jsonl
    (originally called signalmedia-1m.jsonl
    :param int size: if given, this only returns the first x json articles
    and then breaks the loop
    
    :rtype: generator
    :return: generator of json objects
    """
    if end:
        line_range = range(start, end+1)

    with open(path_signalmedia_json) as infile:
        for counter, line in enumerate(infile, 1):

            if end:
                if counter not in line_range:
                    continue            
                if counter > end:
                    break
	
            article = json.loads(line)
            yield article
                
def load_article_into_newsitem_class(article):
    """
    load json article into semeval_classes.NewsItem
    
    :param dict article: json of signalmedia article (dict in python)
    
    :rtype: semeval_classes.NewsItem
    :return: semeval_classes.NewsItem with relevant attributes set
    """
    identifier = article['id']
    
    a_news_item = semeval_classes.NewsItem(
        identifier = identifier,
        collection = 'SignalMedia',
        dct = article['published'],
        publisher = article['source'])
    
    # add entity mention
    naf = spacy_to_naf.text_to_NAF(article['content'], nlp)

    iden2wf_el = {int(wf_el.get('id')[1:]) : wf_el
                  for wf_el in naf.iterfind('text/wf')}
    for entity_el in naf.iterfind('entities/entity'):
        entity_type = entity_el.get('type')
        idens = [int(t_id.get('id')[1:]) 
                 for t_id in entity_el.iterfind('references/span/target')]
        
        # get mention
        mention = ' '.join([iden2wf_el[iden].text
                            for iden in idens])
        
        # get sentence id
        sent_ids = [iden2wf_el[iden].get('sent')
                    for iden in idens]
        assert len(set(sent_ids)) == 1, 'in %s, entity in multiple sentences' % article['content']
        sent_id = sent_ids[0]
        
        # get start and end offset
        wf_el = iden2wf_el[idens[0]]
        begin_index = int(wf_el.get('offset'))
        
        if len(idens) == 1:
            end_index = begin_index + int(wf_el.get('length'))
        else:
            end_wf_el = iden2wf_el[idens[-1]]
            end_index = int(end_wf_el.get('offset')) + int(end_wf_el.get('length'))

        entity_mention_obj = semeval_classes.EntityMention(
            sentence=sent_id,
            mention=mention,
            the_type=entity_type,
            begin_index=begin_index,
            end_index=end_index)
        a_news_item.entity_mentions.add(entity_mention_obj)
    
    return a_news_item

sentenceURI=URIRef("http://longtailcorpus.org/vocab/sent")
NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
newsItemType=URIRef("http://longtailcorpus.org/NewsItem")
entityType=URIRef("http://longtailcorpus.org/Entity")

def rdfize_news_item(a_news_item, g):
    """
    convert instance of semeval_classes.NewsItem into RDF
    
    :param semeval_classes.NewsItem a_news_item: instance of semeval_classes.NewsItem
    """
    news_item_id = a_news_item.identifier
    # create URI for this news item
    newsItemURIString = "http://longtailcorpus.org/news/%s" % news_item_id
    newsItem = URIRef(newsItemURIString)

    # Add the news item triples to the graph
    g.add(( newsItem, DCTERMS.source, Literal(news_item_id) ))
    g.add(( newsItem, DCTERMS.isPartOf, Literal(a_news_item.collection) ))
    dct=datetime.datetime.strptime(a_news_item.dct, '%Y-%m-%dT%H:%M:%SZ') # 2015-09-04T10:43:03Z
    g.add(( newsItem, DCTERMS.created, Literal(dct)))
    g.add(( newsItem, DCTERMS.publisher, Literal(a_news_item.publisher)))
    g.add(( newsItem, RDF.type, newsItemType))

    # iterate through the entity mentions
    for entity_mention_obj in a_news_item.entity_mentions:
        # create URI for this entity mention
        entityMentionURIString="%s#char=%d,%d" % (newsItemURIString, 
                                                  entity_mention_obj.begin_index,
                                                  entity_mention_obj.end_index)
        entityMentionURI=URIRef(entityMentionURIString)

        # add entity mention triples
        g.add((entityMentionURI, NIF.anchorOf, Literal(entity_mention_obj.mention)))
        g.add((entityMentionURI, RDF.type, Literal(entity_mention_obj.the_type)))
        g.add((entityMentionURI, NIF.beginIndex, Literal(entity_mention_obj.begin_index)))
        g.add((entityMentionURI, NIF.endIndex, Literal(entity_mention_obj.end_index)))
        g.add((entityMentionURI, sentenceURI, Literal(int(entity_mention_obj.sentence))))
        g.add((entityMentionURI, RDF.type, entityType))
        g.add((newsItem, URIRef("http://longtailcorpus.org/vocab/hasMention"), entityMentionURI))

    return g
    
def json2rdf(article, g):
    """
    convert json article into rdf (saved in 'signalmedia_rdf')
    
    :param dict article: json of signalmedia article (dict in python)
    """
    a_news_item = load_article_into_newsitem_class(article)
    g = rdfize_news_item(a_news_item, g)
    return g
    
