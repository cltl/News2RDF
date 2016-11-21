class EntityMention:
    """
    class containing information about an entity mention
    """

    def __init__(self, sentence, mention,
                 the_type, 
                 begin_index, end_index,
                 meaning=None):
        self.sentence = sentence         # e.g. 4 -> which sentence is the entity mentioned in
        self.mention = mention           # e.g. "John Smith" -> the mention of an entity as found in text
        self.the_type = the_type         # e.g. "Person" | "http://dbpedia.org/ontology/Person"
        self.meaning = meaning           # e.g. "http://dbpedia.org/resource/John_Smith" | empty if the data has no entity disambiguation layer
        self.begin_index = begin_index   # e.g. 15 -> begin offset
        self.end_index = end_index       # e.g. 25 -> end offset


class ConceptMention:
    """
    class containing information about a concept mention
    """
    def __init__(self, sentence, mention,
                 lemma, mention_offset_ranges,
                 meaning=None):
        self.sentence = sentence        # e.g. 6 -> which sentence is the concept mentioned in
        self.mention = mention          # e.g. "spies" -> the expression of a concept as found in text
        self.lemma = lemma              # e.g. "spy" -> lemmatized form of the expression
        self.meaning = meaning          # e.g. "http://www.newsreader-project.eu/wordnet/ili-30-00890590-v" | Or empty if the data has no concept disambiguation layer
        self.mention_offset_ranges = mention_offset_ranges # e.g. list of range()


class EventMention:
    """
    class containing information about an event mention
    """
    def __init__(self, sentence, mention,
             lemma, mention_offset_ranges,
             meaning=None):
        self.sentence = sentence        # e.g. 6 -> which sentence is the event mentioned in
        self.mention = mention          # e.g. "enabled" -> the expression of an event as found in text
        self.lemma = lemma              # e.g. "enable" -> lemmatized form of the expression
        self.meaning = meaning          # e.g. "http://longtailcorpus.org/news/1111-2222-3333-4444#ev3" # some kind of disambiguation identifier
        self.mention_offset_ranges = mention_offset_ranges # e.g. list of range()


class NewsItem:
    """
    class containing information about a news item
    """
    def __init__(self, identifier, collection,
                 dct, publisher, 
                 location=None, domain=None):
        self.identifier = identifier  # string, the original document name in the dataset
        self.collection = collection  # which collection does it come from (one of ECB+, SignalMedia, or some WSD dataset)
        self.dct = dct                # e.g. "2005-05-14T02:00:00.000+02:00" -> document creation time
        self.publisher = publisher    # e.g. "Reuters" -> Who is the publisher of the document (e.g. Reuters)
        self.location = location      # e.g.  "UK" -> What is the location of the publisher (e.g. UK)
        self.domain = domain          # e.g. "crime"  -> one of the topics/domains (we could also use URI identifiers for these if we want to keep more information)
        self.validated = False        # e.g. False -> whether the document is validated
        self.entity_mentions = set()  # set of instances of EntityMention class
        self.concept_mentions = set() # set of instances of ConceptMention class
        self.event_mentions = set()   # set of instances of EventMention class
