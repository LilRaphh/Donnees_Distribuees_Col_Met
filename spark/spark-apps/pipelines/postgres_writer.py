class PostgresWriter:
    def __init__(self, url, table, user, password, driver):
        self.url = url
        self.table = table
        self.user = user
        self.password = password
        self.driver = driver

    def write_to_postgres(self, batch_df, batch_id):
        try:
            count = batch_df.count()
            batch_df.write \
                .format("jdbc") \
                .option("url", self.url) \
                .option("dbtable", self.table) \
                .option("user", self.user) \
                .option("password", self.password) \
                .option("driver", self.driver) \
                .mode("append") \
                .save()
            print(f"[Batch {batch_id}] ✅ {count} lignes écrites dans PostgreSQL")
        except Exception as e:
            print(f"[Batch {batch_id}] ❌ Erreur écriture PostgreSQL : {e}")
