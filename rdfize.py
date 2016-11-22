import pickle
import semeval_classes
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, FOAF, DC, DCTERMS
import datetime


sentenceURI=URIRef("http://longtailcorpus.org/vocab/sent")
NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
def rdfize_news_item(news_item_id, news_items, collection): # Parse news item to RDF
	a_news_item = news_items[news_item_id]

	# create URI for this news item
	newsItemURIString = "http://longtailcorpus.org/news/%s" % news_item_id
	newsItem = URIRef(newsItemURIString)
	
	# initialize an empty graph
	g = Graph()

	# Add the news item triples to the graph
	g.add(( newsItem, DCTERMS.source, Literal(news_item_id) ))
	g.add(( newsItem, DCTERMS.isPartOf, Literal(collection) ))
	dct=datetime.datetime.strptime(getattr(a_news_item, 'dct'), '%Y-%m-%dT%H:%M:%SZ') # 2015-09-04T10:43:03Z
	g.add(( newsItem, DCTERMS.created, Literal(dct)))
	g.add(( newsItem, DCTERMS.publisher, Literal(getattr(a_news_item,'publisher'))))

	# iterate through the entity mentions
	for entity_mention_obj in a_news_item.entity_mentions:
		# create URI for this entity mention
		entityMentionURIString="%s#char=%d,%d" % (newsItemURIString, getattr(entity_mention_obj, 'begin_index'), getattr(entity_mention_obj, 'end_index'))
		entityMentionURI=URIRef(entityMentionURIString)

		# add entity mention triples
		g.add(( entityMentionURI, NIF.anchorOf, Literal(getattr(entity_mention_obj, 'mention')) ))
		g.add((entityMentionURI, RDF.type, Literal(getattr(entity_mention_obj, 'the_type'))))
		g.add((entityMentionURI, NIF.beginIndex, Literal(getattr(entity_mention_obj, 'begin_index'))))
		g.add((entityMentionURI, NIF.endIndex, Literal(getattr(entity_mention_obj, 'end_index'))))
		g.add((entityMentionURI, sentenceURI, Literal(int(getattr(entity_mention_obj, 'sentence')))))

	g.serialize(destination=news_item_id + '.ttl', format='turtle')
