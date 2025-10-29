from pyspark.sql.functions import col

class KafkaReader:
    def __init__(self, spark, servers, topic):
        self.spark = spark
        self.servers = servers
        self.topic = topic

    def read_stream(self):
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.servers) \
            .option("subscribe", self.topic) \
            .option("startingOffsets", "latest") \
            .load()
        print("✅ Lecture Kafka initialisée")
        return df.selectExpr("CAST(value AS STRING) as json_value")
