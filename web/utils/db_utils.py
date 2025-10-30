import psycopg2

def get_metrics_for_endpoint(app_name, endpoint_name):
    # Exemple simple : nombre de lignes dans la table correspondante
    table_map = {
        ("OpenSky", "positions"): "opensky_positions",
        ("OpenSky", "aircrafts"): "opensky_aircrafts",
    }
    table = table_map.get((app_name, endpoint_name))
    if not table:
        return {}

    conn = psycopg2.connect(
        dbname="donneeDistrib_db",
        user="skayne",
        password="admin",
        host="donneeDistrib_postgres",
        port=5432
    )
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"rows": count}
