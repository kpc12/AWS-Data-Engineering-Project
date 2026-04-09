import json
import uuid
import random
from datetime import datetime, timedelta, timezone

first_names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank"]
last_names  = ["Smith", "Jones", "Lee", "Brown", "Davis", "Wilson", "Moore"]
cities      = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
states      = ["NY", "CA", "IL", "TX", "AZ", "FL", "WA"]
hobbies     = ["reading", "gaming", "cycling", "cooking", "hiking", "painting"]
statuses    = ["pending", "completed", "cancelled", "refunded"]

def make_order(is_late=False, order_id=None):
    """Build and return one order dict."""
    now        = datetime.now(timezone.utc)
    order_time = (now - timedelta(seconds=10)) if is_late else now
 
    return {
        "order_id":   order_id or str(uuid.uuid4()),
        "first_name": random.choice(first_names),
        "last_name":  random.choice(last_names),
        "age":        random.randint(18, 65),
        "city":       random.choice(cities),
        "state":      random.choice(states),
        "hobby":      random.choice(hobbies),
        "status":     random.choice(statuses),
        "is_active":  random.choice([True, False]),
        "amount":     random.randint(100, 1000),
        "quantity":   random.randint(1, 5),
        "score":      round(random.uniform(1.0, 100.0), 2),
        "date":       order_time.isoformat(),
        "created_at": now.isoformat(),
    }
def produce(queue):
    normal_ids = []
    for _ in range(10):
        order = make_order()
        queue.append(order)
        normal_ids.append(order["order_id"])

    for oid in normal_ids[:3]:
        order = make_order(order_id=oid)
        queue.append(order)

    for _ in range(3):
        order = make_order(is_late=True)
        queue.append(order)

    random.shuffle(queue)

def extract(queue):
    print("[ EXTRACT ]")
    orders = list(queue)          # take a snapshot of the queue
    print(f"  Read {len(orders)} orders from queue\n")
    return orders

