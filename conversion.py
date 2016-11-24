import utils
from datetime import datetime
import argparse

from rdflib import Graph

parser = argparse.ArgumentParser(description='''Convert SignalMedia to RDF.''')
parser.add_argument('-f', type=int, dest="start_line", help="convert from line number", required=True)
parser.add_argument('-t', type=int, dest="end_line",   help="convert till line number (inclusive)", required=True)
parser.add_argument('-s', type=int, dest="batch_size",   help="batch size", required=True)

args = parser.parse_args()

path_signalmedia_json = 'signalmedia-1m.jsonl'

for start in range(args.start_line, args.end_line, args.batch_size):
    end = start + args.batch_size

    exp_basename='%s_%s' % (start, end)
    log_path = 'logs/%s.log' % exp_basename
    output_path = 'signalmedia_big_rdf/%s.ttl' % exp_basename

    g=Graph()
    logger = utils.start_logger(log_path)

    json_generator = utils.process_first_x_files(path_signalmedia_json, 
                                                 start=start,
                                                 end=end)

    for counter, article in enumerate(json_generator, start): 
        g=utils.json2rdf(article, g)

        if counter % 100 == 0:
            logger.info('processed %s files' % counter)

    g.serialize(destination=output_path, format='turtle')
