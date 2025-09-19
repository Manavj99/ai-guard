from src.ai_guard.performance import batch_process

def process_item(item):
    return item * 2

items = [1, 2, 3, 4, 5]
results = batch_process(items, processor=process_item, batch_size=2)
print('Results:', results)
print('Length:', len(results))
