import subprocess

def run_spark_job(endpoint_name):
    # mapping endpoint -> script spark
    scripts = {
        "OpenSky/positions": "/opt/spark/work-dir/airtraffic_etl.py",
        # ajouter d'autres endpoints
    }
    script = scripts.get(endpoint_name)
    if not script:
        print(f"No Spark script found for {endpoint_name}")
        return

    cmd = [
        "docker", "exec", "-it", "spark-master",
        "/opt/spark/bin/spark-submit",
        "--master", "spark://spark-master:7077",
        "--packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3",
        "--conf", "spark.driver.extraJavaOptions=-Duser.home=/tmp -Dlog4j.configuration=file:/dev/null",
        "--conf", "spark.executor.extraJavaOptions=-Duser.home=/tmp",
        script
    ]
    subprocess.run(cmd)
