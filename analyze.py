import pprint
from aggregate import aggregate_data
import json
import os.path

aggregate_filename = "aggregate.json"

# load from JSON checkpoint if available
if not os.path.isfile(aggregate_filename):
    data = aggregate_data()

    with open(aggregate_filename, "w") as f:
        json.dump(data, f)

else:
    with open(aggregate_filename, "r") as f:
        data = json.load(f)

all_products = set()

for key, val in data.items():
    for name in val.keys():
        all_products.add(name)

pprint.pprint(all_products)
print(len(all_products))

pprint.pprint(data)
