import utils

path_signalmedia_json = 'signalmedia-1m.jsonl'
size = 1000
json_generator = utils.process_first_x_files(path_signalmedia_json, size)

for article in json_generator: 
    utils.json2rdf(article)