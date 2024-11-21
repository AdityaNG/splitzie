
BILL_SPLIT_PROMPT = """You are Splitzie, the bill splitting AI!
- The attached image is a bill.
- Be very careful about looking at the total amount for each item, don't look at the unit price.
- We need to split the bill among all the people. The 
- The user will provide the context to tell you about which people consumed what.
- You must infer from the context what is the list of people.
- You must infer from the image context what are the list of items in the bill
- You must then infer the mapping from people to items (one to many)
- You must make sure that the set of people matches the list of keys in the mapping form people to items
"""

# hi
"""
Following is the template of the python program

```python
bill = {
    'item 1': 10.0,
    'item 2': 10.0,
    'item 3': 10.0,
}
people = [
    'name 1',
    'name 2',
    'name 3',
]
mapping = {
    'name 1': ['item 1'],
    'name 2': ['item 1', 'item 2'],
    'name 3': ['item 3', 'item 1'],
}

# Ensure the set of people in the mapping matches the people list
assert set(people) == set(mapping.keys())

all_items = set()
for name in mapping:
    mapping_item_list = mapping[name]
    for i in mapping_item_list:
        all_items.add(i)

# Ensure all items mapped are in the bill
assert all_items == set(bill.keys())

# Initialize a dictionary to record how many people share each item
item_sharing = {item: 0 for item in bill}

for name, items in mapping.items():
    for item in items:
        item_sharing[item] += 1

print("="*20)
print("BILL SPLIT")
print("="*20)

for name in mapping:
    item_list = mapping[name]
    amount = 0.0
    # Calculate the total amount for the person based on who had what
    for item in item_list:
        # Divide the cost of the item by the number of people sharing it
        amount += bill[item] / item_sharing[item]
    print(name, '\t', amount)

print("="*20)
```

"""