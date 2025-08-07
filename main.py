import redis

client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    password="C5L48",
    decode_responses=True,
)

pubsub = client.pubsub()
pubsub.subscribe("admin_channel")
print("Subscribed to admin_channel")

for message in pubsub.listen():
    print("Message received:", message)
