from pyspark.sql.types import *
from pyspark.sql.functions import explode
import pyspark as ps
import json

def setup(file = 'data/french_tweets.json'):
    global spark, sc
    
    def process_row(row):
        try:
            js = json.loads(row.lower())
            hashtags = [ht['text'] for ht in js['entities']['hashtags']]
            emoji = [] # put Devin's function here
            return js['created_at'], js['text'], hashtags, emoji
        except:
            return "", "", [], []

    spark = (ps.sql.SparkSession
             .builder
             .master('local[6]')
             .appName('twitter-case-study')
             .getOrCreate()
            )
    sc = spark.sparkContext

    schema = StructType( [
        StructField('date',   StringType(),  True),
        StructField('text',   StringType(),  True),
        StructField('hashtag', ArrayType(StringType()),  True),
        StructField('emoji',   ArrayType(StringType()),  True) ] )

    rdd = sc.textFile(file)
    df = rdd.map(process_row).toDF(schema = schema)
    return df


def get_dates(df, tag, ty = 'hashtag'):
    c2 = {'hashtag': 'hash', 'emoji': 'emo'}[ty]
    rows = (df[['date', ty]]
             .withColumn(c2, explode(df[ty]))[['date', c2]]
             .filter(f"{c2} == '{tag}'")[['date']]
             .collect()
            )
    return [row.date for row in rows]


def get_counts(df, ty = "hashtag", amt = 10):
    c2 = {'hashtag': 'hash', 'emoji': 'emo'}[ty]
    rows = (df[['date', ty]]
             .withColumn(c2, explode(df[ty]))[[c2]]
             .groupBy(c2)
             .agg({c2: 'count'})
             .sort(f'count({c2})', ascending=False)
             .take(amt)
            )
    return [(row[c2], row[f'count({c2})']) for row in rows]