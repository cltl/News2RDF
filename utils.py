import json
import logging
import os
from collections import namedtuple, defaultdict

import spacy_to_naf
import semeval_classes 
from spacy.en import English
from lxml import etree
nlp = English()

from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF, DC, OWL, DCTERMS
import datetime
import re

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

def process_first_x_files(path_signalmedia_json,
                          path_newsreader_nafs='',
                          start=None,
                          end=None):
    """
    create generator of json objects (representing signalmedia articles)
    
    :param str path_signalmedia_json: path to all signalmedia article in jsonl
    (originally called signalmedia-1m.jsonl
    :param str path_newsreader_nafs: path to where signalmedia processed
    with pipeline is stored in NAF
    :param int start: start line
    :param int end: end line

    :rtype: generator
    :return: generator of json objects
    """
    if end:
        line_range = range(start, end+1)

    news_item = namedtuple('news_item',
                           ['signalmedia_json', 'preprocessing'])
    path_template = '{path_newsreader_nafs}/{identifier}.in.naf'

    with open(path_signalmedia_json) as infile:
        for counter, line in enumerate(infile, 1):

            if end:
                if counter not in line_range:
                    continue            
                if counter > end:
                    break

            article = json.loads(line)
            identifier = article['id']
            spacy_naf = spacy_to_naf.text_to_NAF(article['content'], nlp)
            the_preprocessing = {('spacy', spacy_naf)}

            if path_newsreader_nafs:
                path_newsreader_naf = path_template.format_map(locals())
                newsreader_naf = etree.parse(path_newsreader_naf)
                if os.path.exists(path_newsreader_naf):
                    the_preprocessing.add(('newsreader', newsreader_naf))

            a_news_item = news_item(signalmedia_json=article,
                                    preprocessing=the_preprocessing)
            yield a_news_item

def create_entity_mention_obj(entity_el, provenance, iden2wf_el, debug=False):
    """
    create EntityMention object

    :param lxml.etree._Element entity_el: entities/entity from NAF
    :param str provenance: spacy | newsreader
    :param dict iden2wf_el: mapping int (no 'w') -> wf element (text/wf)

    :return: semeval_classes.EntityMention
    """
    entity_type = entity_el.get('type')
    idens = [int(t_id.get('id')[1:])
             for t_id in entity_el.iterfind('references/span/target')]

    # get mention
    mention = ' '.join([iden2wf_el[iden].text
                        for iden in idens])

    # get sentence id
    sent_ids = [iden2wf_el[iden].get('sent')
                for iden in idens]
    assert len(set(sent_ids)) == 1, 'entity in multiple sentences'
    sent_id = sent_ids[0]

    # get start and end offset
    wf_el = iden2wf_el[idens[0]]
    begin_index = int(wf_el.get('offset'))

    if len(idens) == 1:
        end_index = begin_index + int(wf_el.get('length'))
    else:
        end_wf_el = iden2wf_el[idens[-1]]
        end_index = int(end_wf_el.get('offset')) + int(end_wf_el.get('length'))

    # find meaning
    xpath_query = 'externalReferences/externalRef[@resource="spotlight_v1"]'
    meaning = ''
    confidence2entity = defaultdict(list)
    for ext_ref_el in entity_el.iterfind(xpath_query):
        confidence = float(ext_ref_el.get('confidence'))
        entity = ext_ref_el.get('reference')
        confidence2entity[confidence].append(entity)

    if confidence2entity:
        max_key = max(confidence2entity)
        if len(confidence2entity[max_key]) == 1:
            meaning = confidence2entity[max_key][0]

    entity_mention_obj = semeval_classes.EntityMention(
        sentence=sent_id,
        mention=mention,
        meaning=meaning,
        the_type=entity_type,
        begin_index=begin_index,
        end_index=end_index,
        provenance=provenance)

    if debug:
        for attr in {'sentence', 'mention', 'meaning', 'the_type',
                     'begin_index', 'end_index', 'provenance'}:
            print(attr, getattr(entity_mention_obj, attr))
        input('continue?')

    return entity_mention_obj


def create_event_mention_obj(predicate_el, provenance,
                             iden2wf_el, tid2lemma,
                             basename,
                             debug=False):
    """
    create instance of class semeval_classes.EventMention

    :param lxml.etree._Element predicate_el: srl/predicate from NAF
    :param str provenance: spacy | newsreader
    :param dict iden2wf_el: mapping int (no 'w') -> wf element (text/wf)
    :param dict tid2lemma: mapping int (no 't') -> lemma
    :param str basename: basename of NAF file

    :return:
    """
    first_span_el = predicate_el.find('span')
    idens = [int(t_id.get('id')[1:])
             for t_id in first_span_el.iterfind('target')]

    # get sentence id
    sent_ids = [iden2wf_el[iden].get('sent')
                for iden in idens]
    assert len(set(sent_ids)) == 1, 'predicate in multiple sentences: %s from %s: %s' % (predicate_el.get('id'), basename, sent_ids)
    sent_id = sent_ids[0]

    # get mention
    mention = ' '.join([iden2wf_el[iden].text
                        for iden in idens])

    # get lemma
    lemma = ' '.join([tid2lemma[iden]
                      for iden in idens])

    mention_offset_ranges = []
    for iden in idens:
        wf_el = iden2wf_el[iden]
        start_offset = int(wf_el.get('offset'))
        end_offset = start_offset + int(wf_el.get('length'))
        mention_offset_ranges.append((start_offset, end_offset))

    an_event_mention_obj = semeval_classes.EventMention(
        sentence=sent_id,
        mention=mention,
        lemma=lemma,
        meaning='',
        mention_offset_ranges=mention_offset_ranges,
        provenance=provenance)

    if debug:
        print()
        print('basename', basename)
        print('predicate id', predicate_el.get('id'))
        for attr in {'sentence', 'mention', 'lemma',
                     'mention_offset_ranges', 'provenance'}:
            print(attr, getattr(an_event_mention_obj, attr))
        input('continue?')

    return an_event_mention_obj

def load_article_into_newsitem_class(info_about_news_item):
    """
    load json article into semeval_classes.NewsItem
    
    :param collections.namedtuple info_about_news_item: namedtuple with as attribute
    1. signammedia_json -> the original json from signalmedia
    2. preprocessing -> set of tuples (provenance, naf)
    
    :rtype: semeval_classes.NewsItem
    :return: semeval_classes.NewsItem with relevant attributes set
    """
    article = info_about_news_item.signalmedia_json
    identifier = article['id']
    
    a_news_item = semeval_classes.NewsItem(
        identifier = identifier,
        collection = 'SignalMedia',
        dct = article['published'],
        publisher = article['source'])
    
    for provenance, naf in info_about_news_item.preprocessing:
        iden2wf_el = {int(wf_el.get('id')[1:]): wf_el
                      for wf_el in naf.iterfind('text/wf')}

        tid2lemma = {int(term_el.get('id')[1:]): term_el.get('lemma')
                     for term_el in naf.iterfind('terms/term')}
        basename = ''
        if provenance == 'newsreader':
            basename = naf.find('nafHeader/fileDesc').get('filename')

        # add entity mentions
        for entity_el in naf.iterfind('entities/entity'):
            entity_mention_obj = create_entity_mention_obj(entity_el, provenance,
                                                           iden2wf_el,
                                                           debug=False)
            a_news_item.entity_mentions.add(entity_mention_obj)

        # add event mentions
        for predicate_el in naf.iterfind('srl/predicate'):
            an_event_mention_obj = create_event_mention_obj(predicate_el,
                                                            provenance,
                                                            iden2wf_el,
                                                            tid2lemma,
                                                            basename,
                                                            debug=False)
            a_news_item.event_mentions.add(an_event_mention_obj)

        # add domain labels
        xpath_query = 'topics/topic[@method="JEX"]'
        jex_domain_labels = {topic_el.text
                             for topic_el in naf.iterfind(xpath_query)}
        a_news_item.domain = jex_domain_labels

    return a_news_item

NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
GAF = Namespace("http://groundedannotationframework.org/gaf#")
CLTLV = Namespace("http://cltl.nl/vocab/")

newsItemType=URIRef("%sContext" % NIF)
cltlPrefix='http://cltl.nl/'
cltlDataPrefix='%sdata/' % cltlPrefix
cltlTopicPrefix='%stopic' % cltlPrefix


def create_publisher_uri(p):
    return ('http://longtailcorpus.org/publisher/%s' % re.sub(r'\W+', '', p))

def create_topic_uri(domain):
    return '%s%s' % (cltlTopicPrefix, domain)

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
    g.add(( newsItem, RDF.type, newsItemType))
    g.add(( newsItem, DCTERMS.source, Literal(news_item_id) ))
    g.add(( newsItem, DCTERMS.isPartOf, URIRef('%s%s' % (cltlDataPrefix, a_news_item.collection)) ))
    dct=datetime.datetime.strptime(a_news_item.dct, '%Y-%m-%dT%H:%M:%SZ') # 2015-09-04T10:43:03Z
    g.add(( newsItem, DCTERMS.created, Literal(dct)))
    g.add(( newsItem, DCTERMS.publisher, URIRef(create_publisher_uri(a_news_item.publisher))))
    if a_news_item.domain:
        g.add(( newsItem, DCT.subject, URIRef(create_topic_uri(a_news_item.domain)) ))

    # iterate through the entity mentions
    for entity_mention_obj in a_news_item.entity_mentions:
        # create URI for this entity mention
        entityMentionURIString="%s#mention=%d,%d" % (newsItemURIString,
                                                  entity_mention_obj.begin_index,
                                                  entity_mention_obj.end_index)
        instanceURI=URIRef("%s#entity=%d,%d" % (newsItemURIString,
                                                  entity_mention_obj.begin_index,
                                                  entity_mention_obj.end_index))
        entityMentionURI=URIRef(entityMentionURIString)

        g.add((entityMentionURI, RDF.type, GAF.Mention))
        # add entity mention triples
        g.add((entityMentionURI, CLTLV.sent, Literal(int(entity_mention_obj.sentence))))
        g.add((entityMentionURI, NIF.anchorOf, Literal(entity_mention_obj.mention)))
#        if entity_mention_obj.lemma:
#            g.add((entityMentionURI, NIF.lemma, Literal(entity_mention.obj.lemma) ))
        g.add(( entityMentionURI, NIF.referenceContext, newsItem ))
        g.add(( entityMentionURI, GAF.denotes, instanceURI ))
        g.add((instanceURI, RDF.type, GAF.Instance))
        g.add((instanceURI, RDF.type, CLTLV.Entity))
        g.add((instanceURI, RDF.type, Literal(entity_mention_obj.the_type)))
        g.add((entityMentionURI, NIF.beginIndex, Literal(entity_mention_obj.begin_index)))
        g.add((entityMentionURI, NIF.endIndex, Literal(entity_mention_obj.end_index)))
        g.add((entityMentionURI, PROV.wasAttributedTo, URIRef('%sprovenance/%s/entity' % (cltlPrefix, entity_mention_obj.provenance)) ))
        if entity_mention_obj.meaning:
            g.add(( instanceURI, OWL.sameAs, URIRef(entity_mention_obj.meaning) ))

    # Iterate through the event mentions
    for event_mention_obj in a_news_item.event_mentions:
        # create URI for this entity mention
        eventMentionURIString="%s#mention=%s" % (newsItemURIString,
                                                  event_mention_obj.mention_offset_ranges)
        instanceURI=URIRef("%s#event=%s" % (newsItemURIString,
                                                  event_mention_obj.mention_offset_ranges))
        eventMentionURI=URIRef(eventMentionURIString)

        g.add((eventMentionURI, RDF.type, GAF.Mention))
        # add entity mention triples
        g.add((eventMentionURI, CLTLV.sent, Literal(int(event_mention_obj.sentence))))
        g.add((eventMentionURI, NIF.anchorOf, Literal(event_mention_obj.mention)))
        if event_mention_obj.lemma:
            g.add((eventMentionURI, NIF.lemma, Literal(event_mention.obj.lemma) ))
        g.add(( eventMentionURI, NIF.referenceContext, newsItem ))
        g.add(( eventMentionURI, GAF.denotes, instanceURI ))
        g.add((instanceURI, RDF.type, GAF.Instance))
        g.add((instanceURI, RDF.type, CLTLV.Event))
        #g.add((instanceURI, RDF.type, Literal(entity_mention_obj.the_type)))
        # TODO: add begin and end offsets
        #g.add((entityMentionURI, NIF.beginIndex, Literal(entity_mention_obj.begin_index)))
        #g.add((entityMentionURI, NIF.endIndex, Literal(entity_mention_obj.end_index)))
        g.add((eventMentionURI, PROV.wasAttributedTo, URIRef('%sprovenance/%s/event' % (cltlPrefix, event_mention_obj.provenance)) ))
        if event_mention_obj.meaning:
            g.add(( instanceURI, OWL.sameAs, URIRef(event_mention_obj.meaning) ))



    return g
    
def json2rdf(article, g):
    """
    convert json article into rdf (saved in 'signalmedia_rdf')
    
    :param dict article: json of signalmedia article (dict in python)
    """
    a_news_item = load_article_into_newsitem_class(article)
    #g = rdfize_news_item(a_news_item, g)
    return g

def locations2rdf():
    j=open('locations.json', 'r')
    locations=json.load(j)
    g=Graph()
    locations_rdf="locations.ttl"
    for publisher in locations:
        pubURI=URIRef(create_publisher_uri(publisher))
        if "homepage" in locations[publisher]:
            g.add((pubURI, FOAF.homepage, URIRef(locations[publisher]["homepage"])))
        g.add((pubURI, DCTERMS.title, Literal(locations[publisher]["name"])))
        if "dbpedia_uri" in locations[publisher]:
            g.add((pubURI, OWL.sameAs, URIRef(locations[publisher]["dbpedia_uri"])))
        if "location_dbpedia_uri" in locations[publisher]:
            g.add((pubURI, DCTERMS.spatial, URIRef(locations[publisher]["location_dbpedia_uri"])))
        g.add((pubURI, RDF.type, URIRef("http://longtailcorpus.org/Publisher")))
        g.serialize(destination=locations_rdf, format='turtle')
    j.close()
