import random
import time
from datetime import datetime
import numpy as np

import psycopg2
import simplejson as json
from confluent_kafka import Consumer, KafkaException, KafkaError, SerializingProducer

from main import delivery_report

conf = {
    'bootstrap.servers': 'localhost:9092',
}

consumer = Consumer(conf | {
    'group.id': 'voting-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
})

POLLING_STATION = ["PS12345", "PS23456", "PS34567", "PS45678", "PS56789", "PS67890", "PS78901", "PS89012", "PS90123", "PS01234", "PS12345", "PS23456", "PS34567", "PS45678", "PS56789", "PS67890", "PS78901", "PS89012", "PS90123", "PS01234", "PS12233"]
VOTE_TYPE = ["regular", "invalid"]

producer = SerializingProducer(conf)


def consume_messages():
    result = []
    consumer.subscribe(['candidates_topic'])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            else:
                result.append(json.loads(msg.value().decode('utf-8')))
                if len(result) == 3:
                    return result

            # time.sleep(5)
    except KafkaException as e:
        print(e)


if __name__ == "__main__":
    conn = psycopg2.connect(host='localhost', dbname='voting', port=5050, user='postgres', password='postgres')
    cur = conn.cursor()

    # candidates
    candidates_query = cur.execute("""
        SELECT row_to_json(t)
        FROM (
            SELECT * FROM candidates
        ) t;
    """)
    candidates = cur.fetchall()
    candidates = [candidate[0] for candidate in candidates]
    if len(candidates) == 0:
        raise Exception("No candidates found in database")
    else:
        print(candidates)

    consumer.subscribe(['voters_topic'])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            elif msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            else:
                voter = json.loads(msg.value().decode('utf-8'))
                chosen_candidate = np.random.choice(candidates)
                vote = voter | chosen_candidate | {
                    "voting_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "vote": 1,
                    "polling_station_id": random.choice(POLLING_STATION),
                    "vote_type": random.choice(VOTE_TYPE)
                }

                try:
                    cur.execute("""
                            INSERT INTO votes (voter_id, candidate_id, timestamp, polling_station_id, vote_type)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (vote['voter_id'], vote['candidate_id'], vote['voting_time'], vote['polling_station_id'], vote['vote_type']))

                    conn.commit()

                    producer.produce(
                        'votes_topic',
                        key=vote["voter_id"],
                        value=json.dumps(vote),
                        on_delivery=delivery_report
                    )
                    producer.poll(0)
                except Exception as e:
                    print("Error: {}".format(e))
                    continue
            time.sleep(2)
    except KafkaException as e:
        print(e)
