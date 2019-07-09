# Configuration related to Cassandra connector & Cluster
# This will probably be done by Pulsar
import findspark
findspark.init()
import os
from pyspark.sql import SQLContext
from pyspark import SparkContext
from pyspark.sql.functions import udf, StringType
from pyspark.sql.functions import mean as sql_mean


# Loads and returns data frame for a table including key space given
def load_and_get_table_df(key_space_name, table_name):
    table_df = sqlContext.read\
        .format('org.apache.spark.sql.cassandra')\
        .options(table=table_name, keyspace=key_space_name)\
        .load()
    return table_df


def second_aggregator(timestamp_second):
    return timestamp_second[:16]+timestamp_second[19:]






def write_df_to_table(table_df, key_space_name, table_name):
    table_df.write \
        .format('org.apache.spark.sql.cassandra') \
        .mode('append') \
        .options(table=table_name, keyspace=key_space_name) \
        .save()

# Unknown if this needs to run every time we call this...
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.datastax.spark:spark-cassandra-connector_2.11:2.3.0 ' \
                                    '--conf spark.cassandra.connection.host=10.0.0.5,' \
                                    '10.0.0.7,10.0.0.12,10.0.0.19 pyspark-shell'

sc = SparkContext('spark://ip-10-0-0-22.ec2.internal:7077', 'cassandra_live_to_minute')
# Creating PySpark SQL Context

sqlContext = SQLContext(sc)

udf_second_aggregator = udf(second_aggregator, StringType())
seconds = load_and_get_table_df('insight', 'twitch_live')
minutes = seconds.groupBy(udf_second_aggregator('timestamp_name').alias('timestamp_name'))\
                          .agg(sql_mean('follower_count').alias('follower_count'))
write_df_to_table(minutes, 'twitch_minute', 'insight')