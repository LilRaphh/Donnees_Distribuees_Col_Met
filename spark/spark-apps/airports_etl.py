from utils.spark_utils import get_spark_session
from utils.kafka_utils import create_kafka_topic
from utils.postgres_utils import check_jdbc_connection
from pipelines.kafka_reader import KafkaReader
from pipelines.transformer import Transformer
from pipelines.postgres_writer import PostgresWriter
import config.settings_airports as settings

# -----------------------------
# 1️⃣ Initialiser Spark
# -----------------------------
spark = get_spark_session()

# -----------------------------
# 2️⃣ Vérifier ou créer le topic Kafka
# -----------------------------
create_kafka_topic(settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_TOPIC)

# -----------------------------
# 3️⃣ Vérifier la connexion PostgreSQL
# -----------------------------
check_jdbc_connection(
    spark,
    settings.POSTGRES_URL,
    settings.POSTGRES_USER,
    settings.POSTGRES_PASSWORD,
    settings.POSTGRES_DRIVER
)

# -----------------------------
# 4️⃣ Lire depuis Kafka
# -----------------------------
reader = KafkaReader(spark, settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_TOPIC)
df_json = reader.read_stream()  # Streaming DataFrame

# -----------------------------
# 5️⃣ Transformer les données
# -----------------------------
transformer = Transformer(spark)
df_airports, df_runways = transformer.transform_airports(df_json)

# -----------------------------
# 6️⃣ Créer le writer PostgreSQL
# -----------------------------
writer_airports = PostgresWriter(
    settings.POSTGRES_URL,
    "airports",
    settings.POSTGRES_USER,
    settings.POSTGRES_PASSWORD,
    settings.POSTGRES_DRIVER
)

writer_runways = PostgresWriter(
    settings.POSTGRES_URL,
    "runways",
    settings.POSTGRES_USER,
    settings.POSTGRES_PASSWORD,
    settings.POSTGRES_DRIVER
)

# -----------------------------
# 7️⃣ Écriture en streaming avec foreachBatch
# -----------------------------
def write_airports_batch(batch_df, batch_id):
    writer_airports.write_to_postgres(batch_df, batch_id)

def write_runways_batch(batch_df, batch_id):
    writer_runways.write_to_postgres(batch_df, batch_id)

query_airports = df_airports.writeStream \
    .foreachBatch(write_airports_batch) \
    .trigger(processingTime='10 seconds') \
    .option("checkpointLocation", "/tmp/checkpoint_airports") \
    .start()

query_runways = df_runways.writeStream \
    .foreachBatch(write_runways_batch) \
    .trigger(processingTime='10 seconds') \
    .option("checkpointLocation", "/tmp/checkpoint_runways") \
    .start()

# -----------------------------
# 8️⃣ Attendre la fin du streaming
# -----------------------------
query_airports.awaitTermination()
query_runways.awaitTermination()
