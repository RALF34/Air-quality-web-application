from bson.code import Code
from datetime import date, datetime, timedelta
from functools import reduce

import numpy as np
import pandas as pd
from pymongo import MongoClient

pollutants = ["O3","NO2","SO2","PM2.5","PM10","CO"]

mongoClient = MongoClient()

database = mongoClient["air_quality"]

stringToDatetime = lambda x: datetime.strptime(x,"%Y/%m/%d %H:%M:%S")

updateList = Code('''
function (history, data_45_days_ago, data_yesterday){
  if (!data_45_days_ago && data_yesterday){
    return history;
  } else if (data_45_days_ago && !data_yesterday){
    return history.slice(1);
  } else {
    const new_data = Array(data_yesterday)
    if (!data_45_days_ago && data_yesterday){
      return history.concat(new_data);
    } else {
      return history.slice(1).concat(new_data);
    }
  }
}
''')

getTimeSlots = Code('''
function (interval, duration){
  const A = Array();
  for (let i = 0; i < interval.length - duration[0] + 1; i++){
    A.push(interval.slice(i,i+duration[0]-1));
  }
  return A;
}
''')

def initialize_database():
    DATE = date.today()
    k = 1
    while k <= 45:
        DATE -= timedelta(days=k)
        url = "https://files.data.gouv.fr/lcsqa/concentrations-de"+\
              "-polluants-atmospheriques-reglementes/temps-reel/"+\
              str(DATE.year)+"/FR_E2_"+DATE.isoformat()+".csv"
        data = pd.read_csv(url,sep=";")
        records = data.to_dict("records")
        for r in records:
			r["dateTime"] = stringToDatetime(r["Date de début"])
			r["date"] = r["dateTime"].date()
			r["hour"] = r["date"].hour
			r["duration"] = []
			r.pop("Date de début")
        database["LCSQA_data"].insert_many(records)
        k += 1
    database["LCSQA_data"].aggregate([
        {"$match": {"validité": 1}},
        {"$rename": 
			{"code station":"station",
			 "Polluant":"pollutant",
			 "valeur brute":"value"}},
        {"$project": 
			{"_id": 0,
			 "station": 1,
			 "pollutant":1,
			 "concentration": 
			 	{"dateTime": "$dateTime",
				 "date": "$date",
				 "hour": "$hour",
				 "value": "$value"},
			"duration": 1}},
        {"$group": 
			{"_id": 
				{"$station": "$station",
			 	 "pollutant": "$pollutant"},
			 "history": 
				{"$push": "$concentration"},
			 "duration": "$duration"}},
        {"$set": {"n_values": {"$size": "$history"},
                  "data_45_days_ago":
                        {"$eq": ["history.$",
                                 date.today()-timedelta(days=45)]}}},
		{"$out": "LCSQA_data"}
	])

def update():
    yesterday = date.today() - timedelta(days=1)
    url = "https://files.data.gouv.fr/lcsqa/concentrations-de"+\
          "-polluants-atmospheriques-reglementes/temps-reel/"+\
          str(yesterday.year)+"/FR_E2_"+yesterday.isoformat()+".csv"
    new_data = read_csv(url,sep=";")
    new_records = new_data.to_dict("records")
    for r in new_records:
		r["dateTime"] = stringToDatetime(r["Date de début"])
		r["date"] = r["dateTime"].date()
		r["hour"] = r["dateTime"].hour
		r["duration"] = []
		r.pop("Date de début")
    database["data_yesterday"].insert_many(new_records)
    database["data_yesterday"].aggregate([
        {"$match": {"validité": 1}},
        {"$project":
			{"_id":
				{"station": "$code station",
				 "pollutant": "$Polluant"},
			 "concentration": 
			 	{"dateTime": "$dateTime",
				 "date": "$date",
				 "hour": "$hour",
				 "value": "$valeur brute"},
			"duration": 1}}
	])
    database["LCSQA_data"].aggregate([
        {"$lookup": 
            {"from": "data_yesterday",
             "localField": "_id",
             "foreignField": "_id",
             "as": "data_yesterday"}},
        {"$addFields": 
            {"history":
                {"$function": 
                    {"body": updateList,
                     "args": ["$history",
                              "$data_45_days_ago",
                              "$data_yesterday"],
                     "lang": "js"}}},
            {"n_values": {"$size": "$history"}},
            {"data_45_days_ago": 
                {"$eq": ["history.$",
                         date.today()-timedelta(days=45)]}}},
		{"$out": "LCSQA_data"}
	])

def get_response(
	station,
	pollutants,
	duration=1,
	period ="0-24",
	n_days=45):
	response = {}
	data = database["LCSQA_data"].find(
		{"_id":station}
	).collection
	start_time, end_time = map(lambda x: int(x), period.split("-"))
	invalid_period = (
		not(start_time in list(range(24))) or
		not(end_time in list(range(1,25))) or
		start_time >= end_time
	)
	if duration >= end_time - start_time:
		response["Best time slots"] = (
			"Unknown (duration too high for the given period)"
		)
		response["Intersection"] = "None"
	elif invalid_period:
		response["Best time slots"] = "Unknown (invalid period)"
		response["Intersection"] = "None"
	else:
		n, m = len(pollutants), end_time-start_time-duration+1
		A = np.ndarray(shape=(n,m), dtype=float)
		hours = list(range(start_time, end_time+1))
		data.update_one({}, {"duration": {"$push": duration}})
		dictionary = {str(i): [] for i in range(hours)}
		for p, i in enumerate(pollutants):
			collection = data.find(
				{"_id.polluant": p,
			 	"hour": {"$in": hours}}
			).sort("dateTime").collection
			for document in collection.aggregate([
				{"$group": 
					{"_id": "$date",
				 	"interval":
				 		{"$push": 
							{"hour": "$hour",
						 	"value": "$value"}},
						 	"duration": "$duration"}},
				{"$project": 
					{"time_slots": 
						{"$function": 
							{"body": getTimeSlots,
						 	"args": ["$interval","$duration"],
						 	"lang": "js"}}}}
				]):
				for e in document["interval"]:
					dictionary[e[0]] += [e[1]]
			for e, j in enumerate(dictionary.keys()):
				A[i][j] = (
					None if not(dictionary[e]) 
					else np.mean(np.array(dictionary[e]))
				)
		indexes = np.nonzero(np.any(np.isnan(A),axis=0))
		if not(indexes[0].size):
			response["Best time slots"] = "Unknown (not enough data)"
			response["Intersection"] = "None"
		else:
			pollutants_with_enough_data = pollutants[indexes]
			X = np.argmin(A[indexes], axis=1)
			slots_with_minimum_pollution = [
				(str(hours[i]) + "h00 - " + 
				 str(hours[i] + duration) + "h00"
				) for i in X
			]
			response["Best time slots"] = {
				k: v for k, v in zip(
					pollutants_with_enough_data,
					slots_with_minimum_pollution
				)
			}
			slots_as_arrays = (
				np.array(
					list(
						map(
							(lambda x:
								np.array(list(range(x[:2],x[7:9])))),
							slot
						)
					)
				) for slot in slots_with_minimum_pollution
			)
			intersection = reduce(np.intersect1d, slots_as_arrays)
			response["Intersection"] = (
				"None" if not(intersection.size)
				else (
					(str(intersection[0]) + "h00 - " +
					 str(intersection[-1]) + "h00"
					)
				)
			)
	return response
