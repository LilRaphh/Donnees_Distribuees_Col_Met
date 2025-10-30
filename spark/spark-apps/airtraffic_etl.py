from utils.spark_utils import get_spark_session
from utils.kafka_utils import create_kafka_topic
from utils.postgres_utils import check_jdbc_connection
from pipelines.kafka_reader import KafkaReader
from pipelines.transformer import Transformer
from pipelines.postgres_writer import PostgresWriter
import config.settings_flight_position as settings

# Initialiser Spark
spark = get_spark_session()

# Vérifier ou créer le topic Kafka
create_kafka_topic(settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_TOPIC)

# Vérifier la connexion PostgreSQL
check_jdbc_connection(spark, settings.POSTGRES_URL, settings.POSTGRES_USER, settings.POSTGRES_PASSWORD, settings.POSTGRES_DRIVER)

# Lire depuis Kafka
reader = KafkaReader(spark, settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_TOPIC)
df_json = reader.read_stream()

# Transformer les données
transformer = Transformer(spark)
df_clean = transformer.transform_flight(df_json)

# Écrire vers PostgreSQL
writer = PostgresWriter(settings.POSTGRES_URL, settings.POSTGRES_TABLE, settings.POSTGRES_USER, settings.POSTGRES_PASSWORD, settings.POSTGRES_DRIVER)

query = df_clean.writeStream \
    .foreachBatch(writer.write_to_postgres) \
    .trigger(processingTime='10 seconds') \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()

query.awaitTermination()
