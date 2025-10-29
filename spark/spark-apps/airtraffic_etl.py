from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode, get_json_object
from pyspark.sql.types import ArrayType, StringType, DoubleType, BooleanType, LongType
from pyspark.sql import DataFrame

# -----------------------------
# 1️⃣ Création de la session Spark
# -----------------------------
spark = SparkSession.builder \
    .appName("OpenSkyETL") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print('SPARK: OKAY')

# -----------------------------
# 2️⃣ Lire les données depuis Kafka
# -----------------------------
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "flights_positions") \
    .option("startingOffsets", "latest") \
    .load()

print('Données kafka: okay')

# -----------------------------
# 3️⃣ Transformer les données
# -----------------------------
# Convertir la valeur en string JSON
df_json = df_raw.selectExpr("CAST(value AS STRING) as json_value")

# Extraire le champ states (tableau de tableaux)
df_states_raw = df_json.select(get_json_object(col("json_value"), "$.states").alias("states_str"))

# Parser states en ArrayType(ArrayType(StringType()))
df_states_array = df_states_raw.select(
    from_json(col("states_str"), ArrayType(ArrayType(StringType()))).alias("states")
)

# Exploser chaque état
df_exploded = df_states_array.select(explode(col("states")).alias("state"))

# Sélectionner les colonnes utiles avec mapping par indices
df_clean = df_exploded.select(
    col("state")[0].alias("icao24"),
    col("state")[1].alias("callsign"),
    col("state")[2].alias("origin_country"),
    col("state")[5].cast("double").alias("longitude"),
    col("state")[6].cast("double").alias("latitude"),
    col("state")[7].cast("double").alias("baro_altitude"),
    col("state")[8].cast("boolean").alias("on_ground"),
    col("state")[9].cast("double").alias("velocity"),
    col("state")[10].cast("double").alias("true_track"),
    col("state")[11].cast("double").alias("vertical_rate"),
    col("state")[13].cast("double").alias("geo_altitude"),
    col("state")[14].alias("squawk"),
    col("state")[15].cast("boolean").alias("spi"),
    col("state")[16].cast("long").alias("position_source")
)

print('Transforme: OKAY')

# -----------------------------
# 4️⃣ Vérification connexion PostgreSQL
# -----------------------------
def check_jdbc_connection():
    try:
        spark.read \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://donneeDistrib_postgres:5432/donneeDistrib_db") \
            .option("dbtable", "(SELECT 1) as t") \
            .option("user", "skayne") \
            .option("password", "admin") \
            .option("driver", "org.postgresql.Driver") \
            .load()
        print("✅ Connexion JDBC OK")
    except Exception as e:
        print(f"❌ Connexion JDBC échouée : {e}")

check_jdbc_connection()
print(f"DF: {df_clean}")

# -----------------------------
# 5️⃣ Écriture dans PostgreSQL
# -----------------------------
def write_to_postgres(batch_df: DataFrame, batch_id: int):
    try:
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://donneeDistrib_postgres:5432/donneeDistrib_db") \
            .option("dbtable", "opensky_positions") \
            .option("user", "skayne") \
            .option("password", "admin") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
        print(f"[Batch {batch_id}] ✅ Batch écrit avec succès ({batch_df.count()} lignes)")
    except Exception as e:
        print(f"[Batch {batch_id}] ❌ Erreur lors de l'écriture : {e}")

query = df_clean.writeStream \
    .foreachBatch(write_to_postgres) \
    .trigger(processingTime='10 seconds') \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()

# Attendre 1 minute par exemple, puis arrêter
query.awaitTermination(60)  # 60 secondes
