from pyspark.sql.functions import col, from_json, explode, get_json_object
from pyspark.sql.types import ArrayType, StringType

class Transformer:
    def __init__(self, spark):
        self.spark = spark

    def transform(self, df_json):
        df_states_raw = df_json.select(get_json_object(col("json_value"), "$.states").alias("states_str"))
        df_states_array = df_states_raw.select(
            from_json(col("states_str"), ArrayType(ArrayType(StringType()))).alias("states")
        )
        df_exploded = df_states_array.select(explode(col("states")).alias("state"))

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
        print("✅ Transformation OK")
        return df_clean
