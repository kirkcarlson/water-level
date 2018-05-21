#### IMPORTS ####
import datetime

from influxdb import InfluxDBClient

#### GLOBALS ####
influxClient = None
influxWrites = 0


def init( databaseName):
  global influxClient

  # initialize influxdb channel
  influxClient = InfluxDBClient(host='localhost', port=8086)
  if databaseName not in influxClient.get_list_database():
    influxClient.create_database( databaseName)
    influxClient.create_retention_policy("keep forever", "INF", 1,
        database=databaseName)
  influxClient.switch_database( databaseName)


def sendMeasurementLevel( currentTick, measurement, fieldType, level):
  global influxClient
  global influxWrites

  influxWrites = influxWrites + 1
  influxClient.write_points (
    [ {
      "measurement" : measurement,
      #"time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
      "time": "{0:%Y-%m-%dT%H:%M:%S.%f-0400}".format(
                datetime.datetime.fromtimestamp(currentTick)),
      "fields" : {
        fieldType : level+0.
      }
    } ]
  )


def sendTaggedMeasurementLevel( currentTick, measurement, tagType, tag, fieldType, level):
  global influxClient
  global influxWrites

  influxWrites = influxWrites + 1
  influxClient.write_points (
    [ {
      "measurement" : measurement,
      "tags" : {
          tagType : tag
      },
      #"time": "{0:%Y-%m-%dT%H:%M:%S.%fZ-04}".format(
      "time": "{0:%Y-%m-%dT%H:%M:%S.%f-0400}".format(
                datetime.datetime.fromtimestamp(currentTick)),
      "fields" : {
         fieldType : level+0.
      }
    } ]
  )
