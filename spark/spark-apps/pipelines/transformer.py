from pyspark.sql.functions import col, from_json, explode, get_json_object, lit, to_json, current_timestamp
from pyspark.sql.types import ArrayType, StringType, StructField, StructType, DoubleType, BooleanType, LongType

class Transformer:
    def __init__(self, spark):
        self.spark = spark

    def transform_flight(self, df_json):
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
            col("state")[16].cast("long").alias("position_source"),
            current_timestamp().alias("ingestion_time")
        )
        print("✅ Transformation OK")
        return df_clean

    def transform_airports(self, df_json):
        # Étape 1 : extraire la chaîne JSON de la liste d’aéroports
        df_items_raw = df_json.select(
            get_json_object(col("json_value"), "$.items").alias("items_str")
        )

        # Étape 2 : parser la liste d’aéroports
        df_items_array = df_items_raw.select(
            from_json(col("items_str"), ArrayType(StringType())).alias("items")
        )

        # Étape 3 : exploser pour obtenir chaque aéroport en JSON string
        df_exploded = df_items_array.select(
            explode(col("items")).alias("airport_json")
        )

        # Étape 4 : définir le schéma de l’aéroport (simplifié)
        AIRPORT_SCHEMA = StructType([
            StructField("_id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("type", LongType(), True),
            StructField("trafficType", ArrayType(LongType()), True),
            StructField("magneticDeclination", DoubleType(), True),
            StructField("country", StringType(), True),
            StructField("geometry", StructType([
                StructField("type", StringType(), True),
                StructField("coordinates", ArrayType(DoubleType()), True)
            ]), True),
            StructField("elevation", StructType([
                StructField("value", DoubleType(), True),
                StructField("unit", LongType(), True),
                StructField("referenceDatum", LongType(), True)
            ]), True),
            StructField("elevationGeoid", StructType([
                StructField("geoidHeight", DoubleType(), True),
                StructField("hae", DoubleType(), True)
            ]), True),
            StructField("ppr", BooleanType(), True),
            StructField("private", BooleanType(), True),
            StructField("skydiveActivity", BooleanType(), True),
            StructField("winchOnly", BooleanType(), True),
            StructField("runways", ArrayType(
                StructType([
                    StructField("_id", StringType(), True),
                    StructField("designator", StringType(), True),
                    StructField("trueHeading", DoubleType(), True),
                    StructField("alignedTrueNorth", BooleanType(), True),
                    StructField("operations", LongType(), True),
                    StructField("mainRunway", BooleanType(), True),
                    StructField("turnDirection", LongType(), True),
                    StructField("takeOffOnly", BooleanType(), True),
                    StructField("landingOnly", BooleanType(), True),
                    StructField("surface", StructType([
                        StructField("composition", ArrayType(LongType()), True),
                        StructField("mainComposite", LongType(), True),
                        StructField("condition", LongType(), True)
                    ]), True),
                    StructField("dimension", StructType([
                        StructField("length", StructType([
                            StructField("value", DoubleType(), True),
                            StructField("unit", LongType(), True)
                        ]), True),
                        StructField("width", StructType([
                            StructField("value", DoubleType(), True),
                            StructField("unit", LongType(), True)
                        ]), True)
                    ]), True),
                    StructField("declaredDistance", StructType([
                        StructField("tora", StructType([
                            StructField("value", DoubleType(), True),
                            StructField("unit", LongType(), True)
                        ]), True),
                        StructField("lda", StructType([
                            StructField("value", DoubleType(), True),
                            StructField("unit", LongType(), True)
                        ]), True)
                    ]), True),
                    StructField("pilotCtrlLighting", BooleanType(), True)
                ])
            ), True),
            StructField("createdAt", StringType(), True),
            StructField("updatedAt", StringType(), True),
            StructField("createdBy", StringType(), True),
            StructField("updatedBy", StringType(), True),
            StructField("__v", LongType(), True)
        ])

        # Étape 5 : parser chaque aéroport
        df_parsed = df_exploded.select(
            from_json(col("airport_json"), AIRPORT_SCHEMA).alias("airport")
        )

        # Étape 6 : extraire les données pour la table airports
        df_airports = df_parsed.select(
            col("airport._id").alias("api_id"),
            col("airport.name").alias("name"),
            col("airport.type").alias("type"),
            to_json(col("airport.trafficType")).alias("traffic_type"),
            col("airport.magneticDeclination").alias("magnetic_declination"),
            col("airport.country").alias("country"),
            col("airport.geometry.coordinates")[0].alias("longitude"),
            col("airport.geometry.coordinates")[1].alias("latitude"),
            col("airport.elevation.value").alias("elevation_value"),
            col("airport.elevation.unit").alias("elevation_unit"),
            col("airport.elevation.referenceDatum").alias("elevation_reference_datum"),
            col("airport.elevationGeoid.geoidHeight").alias("elevation_geoid_height"),
            col("airport.elevationGeoid.hae").alias("elevation_hae"),
            col("airport.ppr").alias("ppr"),
            col("airport.private").alias("private"),
            col("airport.skydiveActivity").alias("skydive_activity"),
            col("airport.winchOnly").alias("winch_only"),
            col("airport.createdAt").cast("timestamp").alias("created_at"),
            col("airport.updatedAt").cast("timestamp").alias("updated_at"),
            col("airport.createdBy").alias("created_by"),
            col("airport.updatedBy").alias("updated_by"),
            col("airport.__v").alias("version"),
            col("airport.geometry.type").alias("geometry_type")
        )

        # Étape 7 : exploser les pistes pour la table runways
        df_runways = df_parsed.select(
            col("airport._id").alias("airport_api_id"),
            explode(col("airport.runways")).alias("runway")
        ).select(
            col("airport_api_id"),
            col("runway._id").alias("runway_api_id"),
            col("runway.designator").alias("designator"),
            col("runway.trueHeading").alias("true_heading"),
            col("runway.alignedTrueNorth").alias("aligned_true_north"),
            col("runway.operations").alias("operations"),
            col("runway.mainRunway").alias("main_runway"),
            col("runway.turnDirection").alias("turn_direction"),
            col("runway.takeOffOnly").alias("take_off_only"),
            col("runway.landingOnly").alias("landing_only"),
            to_json(col("runway.surface.composition")).alias("surface_composition"),
            col("runway.surface.mainComposite").alias("surface_main_composite"),
            col("runway.surface.condition").alias("surface_condition"),
            col("runway.dimension.length.value").alias("length_value"),
            col("runway.dimension.length.unit").alias("length_unit"),
            col("runway.dimension.width.value").alias("width_value"),
            col("runway.dimension.width.unit").alias("width_unit"),
            col("runway.declaredDistance.tora.value").alias("tora_value"),
            col("runway.declaredDistance.tora.unit").alias("tora_unit"),
            col("runway.declaredDistance.lda.value").alias("lda_value"),
            col("runway.declaredDistance.lda.unit").alias("lda_unit"),
            col("runway.pilotCtrlLighting").alias("pilot_ctrl_lighting")
        )

        print("✅ Transformation des aéroports et pistes OK")
        return df_airports, df_runways