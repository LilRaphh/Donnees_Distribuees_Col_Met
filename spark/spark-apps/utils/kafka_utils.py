from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

def create_kafka_topic(bootstrap_servers: str, topic_name: str):
    try:
        admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
        admin.create_topics([topic])
        print(f"✅ Topic Kafka '{topic_name}' créé")
    except TopicAlreadyExistsError:
        print(f"ℹ️ Topic Kafka '{topic_name}' existe déjà")
    except Exception as e:
        print(f"⚠️ Erreur lors de la création du topic Kafka : {e}")
    finally:
        admin.close()
