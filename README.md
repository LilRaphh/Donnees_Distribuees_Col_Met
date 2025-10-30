# 🚀 Projet M2 Data -- Pipeline ETL Distribué (NiFi / Kafka / Cassandra)

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
  [Apache Cassandra] → stockage distribué
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

  **Cassandra**               Stockage         Base distribuée pour la
                                               persistance et la
                                               consultation des données
                                               agrégées

  **Power BI / Grafana**      Visualisation    Création de tableaux de bord
                                               à partir des données stockées

  **Docker Compose**          Infrastructure   Orchestration des services
                                               (NiFi, Kafka, Spark,
                                               Cassandra, etc.)
  --------------------------------------------------------------------------

------------------------------------------------------------------------

## 🔄 Fonctionnement du pipeline

### 1. **Ingestion -- Apache NiFi**

-   **InvokeHTTP** : appelle l'API (ex. OpenSky) toutes les 10
    secondes.\
-   **EvaluateJsonPath** : extrait les champs pertinents (`timestamp`,
    `icao24`, `lat`, `lon`, `altitude`, `velocity`, etc.).\
-   **AttributesToJSON** : reformate les données en JSON.\
-   **PublishKafkaRecord_2\_0** : envoie les messages vers le topic
    Kafka `flights_positions`.

### 2. **Streaming -- Apache Kafka**

-   Centralise les messages reçus.\

-   Vérification possible via :

    ``` bash
    kafka-console-consumer --bootstrap-server kafka:9092 --topic flights_positions --from-beginning
    ```

### 3. **Traitement -- Apache Spark**

-   Lecture du flux Kafka en temps réel :

    ``` python
    df = spark       .readStream       .format("kafka")       .option("kafka.bootstrap.servers", "kafka:9092")       .option("subscribe", "flights_positions")       .load()
    ```

-   Nettoyage et jointure avec tables de référence (AirLabs / CSV).

-   Calculs typiques :

    -   Nombre de vols actifs par pays.
    -   Vitesse moyenne par zone géographique.
    -   Détection d'altitudes incohérentes.

### 4. **Stockage -- Apache Cassandra**

-   Création d'une **keyspace** et d'une **table flights_agg** :

    ``` sql
    CREATE KEYSPACE flights WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    CREATE TABLE flights.flights_agg (
        flight_id text PRIMARY KEY,
        country text,
        avg_speed float,
        altitude int,
        timestamp timestamp
    );
    ```

-   Écriture depuis Spark :

    ``` python
    df.writeStream     .format("org.apache.spark.sql.cassandra")     .option("keyspace", "flights")     .option("table", "flights_agg")     .start()
    ```

### 5. **Visualisation**

-   Connexion à Cassandra (connecteur ODBC / natif).\
-   Exemples :
    -   Carte des positions d'avions (lat/lon).
    -   Graphiques de vitesse moyenne.
    -   Nombre de vols actifs en temps réel.

------------------------------------------------------------------------

## 🧱 Structure du dépôt

    📁 projet-m2-data/
    ├── docker-compose.yml
    ├── nifi_template.xml
    ├── spark/
    │   ├── stream_processing.py
    │   └── requirements.txt
    ├── cassandra/
    │   ├── init.cql
    │   └── config/
    ├── docs/
    │   ├── architecture.png
    │   └── notes.md
    └── README.md

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
docker exec -it spark-master spark-submit /opt/spark/app/stream_processing.py
```

### 6. Visualiser les résultats

-   Se connecter à Cassandra avec Power BI / Grafana.\
-   Charger les tables `flights_agg`.

------------------------------------------------------------------------

## 🗝️ APIs utilisées

-   [OpenSky Network](https://opensky-network.org/apidoc)
-   [AirLabs](https://airlabs.co/docsl)
-   [OpenAIP](https://docs.openaip.net)

------------------------------------------------------------------------

## 🧠 Auteurs

Projet réalisé dans le cadre du **Master 2 Data Science**\
**Durée :** 1 semaine --- **Travail en binôme**
