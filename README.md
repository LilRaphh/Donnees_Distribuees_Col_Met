# 🚀 Projet M2 Data -- Pipeline ETL Distribué (NiFi / Kafka / Postgres)

## 📌 Contexte

Ce projet consiste à mettre en place une chaîne complète **ETL
distribuée** en environnement **Docker**, permettant de collecter,
transformer et stocker en quasi temps réel des **données aériennes
issues d'API publiques**.\
L'objectif est de démontrer la capacité à gérer un flux de données
massives et à produire des indicateurs exploitables dans un outil de
visualisation.

------------------------------------------------------------------------

## 🧩 Architecture globale

``` text
API (OpenSky / AirLabs / OpenAIP)
        │
        ▼
  [Apache NiFi] → ingestion
        │ (PublishKafkaRecord)
        ▼
  [Apache Kafka] → streaming distribué
        │ (Topic: flights_positions)
        ▼
  [Apache Spark Streaming] → traitement & agrégation
        │
        ▼
  [Postgres] → stockage distribué → Visualisation dans PgAdmin
        │
        ▼
  [Power BI / Grafana] → visualisation
```

------------------------------------------------------------------------

## ⚙️ Technologies utilisées

  --------------------------------------------------------------------------
  Composant                   Rôle             Description
  --------------------------- ---------------- -----------------------------
  **NiFi**                    Ingestion        Récupération périodique du
                                               flux (InvokeHTTP), extraction
                                               JSON et publication dans
                                               Kafka

  **Kafka**                   Message broker   Centralise le flux temps réel
                                               (`flights_positions`)

  **Spark Structured          Traitement       Lecture continue du flux
  Streaming**                                  Kafka, nettoyage, jointures
                                               et calculs

  **Postgres**                Stockage         Base distribuée pour la
                                               persistance et la
                                               consultation des données
                                               agrégées

  **Grafana**                 Visualisation    Création de tableaux de bord
                                               à partir des données stockées

  **Docker**                  Infrastructure   Orchestration des services
                                               (NiFi, Kafka, Spark,
                                               Postgres, etc.)
  --------------------------------------------------------------------------

------------------------------------------------------------------------

## 🔄 Fonctionnement du pipeline

### 1. **Ingestion -- Apache NiFi**

-   **InvokeHTTP** : appelle l'API (ex. OpenSky) toutes les 10
    secondes.
-   **EvaluateJsonPath** : extrait les champs pertinents.
-   **AttributesToJSON** : reformate les données en JSON.
-   **PublishKafkaRecord_2\_0** : envoie les messages vers le topic
    Kafka `{topic}`.

### 2. **Streaming -- Apache Kafka**

-   Centralise les messages reçus.\

-   Vérification possible via :

    ``` bash
    kafka-console-consumer --bootstrap-server kafka:9092 --topic flights_positions --from-beginning
    ```

### 3. **Traitement -- Apache Spark**

-   Lecture du flux Kafka en temps réel :

    ``` python
    df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka:9092").option("subscribe", "flights_positions").load()
    ```

-   Nettoyage et jointure avec tables de référence (AirLabs / CSV).

-   Calculs typiques :

    -   Nombre de vols actifs par pays.
    -   Vitesse moyenne par zone géographique.
    -   Détection d'altitudes incohérentes.

### 4. **Stockage -- Postgres**

-   Création des tables **airports, runways, opensky_positions**

-   Écriture depuis Spark

### 5. **Visualisation**

-   Connexion à Postgres (connecteur ODBC / natif).\
-   Exemples :
    -   Carte des positions d'avions (lat/lon).
    -   Graphiques de vitesse moyenne.
    -   Nombre de vols actifs en temps réel.

------------------------------------------------------------------------

## 🧱 Structure du dépôt

        ├── Donnees_Distribuees_Col_Met
        │   ├── grafana
        │   │   └── docker-compose.yml
        │   ├── kafka
        │   │   ├── docker-compose.yml
        │   │   └── offsetexplorer.sh
        │   ├── modelisation
        │   │   ├── client.json
        │   │   ├── clients_compl.csv
        │   │   ├── docker-compose.yml
        │   │   ├── drivers
        │   │   ├── nifi_data
        │   │   └── clients_compl.csv
        │   ├── README.md
        │   ├── spark
        │   │   ├── docker-compose.yml
        │   │   ├── dockerfile
        │   │   └── spark-apps
        │   │       ├── airports_etl.py
        │   │       ├── airtraffic_etl.py
        │   │       ├── config
        │   │       │   ├── settings_airports.py
        │   │       │   └── settings_flight_position.py
        │   │       ├── pipelines
        │   │       │   ├── kafka_reader.py
        │   │       │   ├── postgres_writer.py
        │   │       │   └── transformer.py
        │   │       ├── requirements.txt
        │   │       └── utils
        │   │           ├── kafka_utils.py
        │   │           ├── postgres_utils.py
        │   │           └── spark_utils.py
        │   └── web
        │       ├── app.py
        │       ├── templates
        │       │   ├── app.html
        │       │   ├── dashboard.html
        │       │   ├── index.html
        │       │   └── layout.html
        │       └── utils
        │           ├── db_utils.py
        │           └── spark_utils.py

------------------------------------------------------------------------

## ▶️ Lancement du projet

### 1. Cloner le dépôt

``` bash
git clone https://github.com/<user>/projet-m2-data.git
cd projet-m2-data
```

### 2. Démarrer l'environnement

``` bash
docker compose up -d
```

### 3. Importer le flux NiFi

-   Accéder à <http://localhost:8080/nifi>
-   Importer `nifi_template.xml`
-   Lancer le flux.

### 4. Vérifier Kafka

``` bash
docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092
```

### 5. Lancer Spark Streaming

``` bash
docker exec -it spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 --conf spark.driver.extraJavaOptions="-Duser.home=/tmp -Dlog4j.configuration=file:/dev/null" --conf spark.executor.extraJavaOptions="-Duser.home=/tmp" /opt/spark/work-dir/airtraffic_etl.py
```

### 6. Visualiser les résultats

-   Se connecter à Cassandra avec / Grafana.\
-   Charger les tables `flights_agg`.

<img width="1690" height="879" alt="image" src="https://github.com/user-attachments/assets/f3559233-305d-4eb9-8f91-8fb2f9532663" />

<img width="1690" height="879" alt="image" src="https://github.com/user-attachments/assets/2b614ff7-408b-4c05-b3ef-72d7fa75d6b2" />



------------------------------------------------------------------------

## 🗝️ APIs utilisées

-   [OpenSky Network](https://opensky-network.org/apidoc)
-   [AirLabs](https://airlabs.co/docsl)
-   [OpenAIP](https://docs.openaip.net)

------------------------------------------------------------------------

## 🧠 Auteurs

Projet réalisé dans le cadre du **Master 2 Data Science**\
**Durée :** 1 semaine --- **Travail en binôme**
