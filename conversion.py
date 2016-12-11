import utils
import argparse

from rdflib import Graph

parser = argparse.ArgumentParser(description='''Convert SignalMedia to RDF.''')
parser.add_argument('-f', type=int, dest="start_line", help="convert from line number", required=True)
parser.add_argument('-t', type=int, dest="end_line",   help="convert till line number (inclusive)", required=True)
parser.add_argument('-s', type=int, dest="batch_size",   help="batch size", required=True)

args = parser.parse_args()

path_signalmedia_json = 'signalmedia-1m.jsonl'
path_newsreader_nafs = 'naf'

for start in range(args.start_line, args.end_line, args.batch_size):
    end = start + args.batch_size

    exp_basename='%s_%s' % (start, end)
    log_path = 'logs/%s.log' % exp_basename
    output_path = 'signalmedia_big_rdf/%s.ttl' % exp_basename

    g=Graph()
    logger = utils.start_logger(log_path)

    the_generator = utils.process_first_x_files(path_signalmedia_json,
                                                path_newsreader_nafs=path_newsreader_nafs,
                                                start=start,
                                                end=end)

    for counter, info_about_news_item in enumerate(the_generator, start):
        g=utils.json2rdf(info_about_news_item, g)
        break
        #if counter % 100 == 0:
        #    logger.info('processed %s files' % counter)

    g.serialize(destination=output_path, format='turtle')
