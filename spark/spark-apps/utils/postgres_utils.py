def check_jdbc_connection(spark, url, user, password, driver):
    try:
        spark.read \
            .format("jdbc") \
            .option("url", url) \
            .option("dbtable", "(SELECT 1) AS t") \
            .option("user", user) \
            .option("password", password) \
            .option("driver", driver) \
            .load()
        print("✅ Connexion JDBC PostgreSQL OK")
        return True
    except Exception as e:
        print(f"❌ Connexion PostgreSQL échouée : {e}")
        return False
