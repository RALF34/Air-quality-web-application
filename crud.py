from bson.code import Code
from datetime import date, datetime, timedelta
from statistics import mean

from matplotlib import pyplot
from pandas import read_csv, read_excel
from pymongo import MongoClient

from dictionaries import french_departments, air_pollutants

mongoClient = MongoClient()

stringToDatetime = lambda x: datetime.strptime(x,"%Y/%m/%d %H:%M:%S")

def create_tables(n_days):
    database = mongoClient["air_quality"]
    DATE = date.today()
    k = 1
    while k <= n_days:
        DATE -= timedelta(days=k)
        url = "https://files.data.gouv.fr/lcsqa/concentrations-de"+\
              "-polluants-atmospheriques-reglementes/temps-reel/"+\
              str(DATE.year)+"/FR_E2_"+DATE.isoformat()+".csv"
        data = read_csv(url, sep=";")
        records = data[data["validité"]==1].to_dict("records")
        for r in records:
            r["date"] = stringToDatetime(r["Date de début"])
            r.pop("Date de début")
            r["hour"] = r["date"].hour
        database["LCSQA_data"].insert_many(records)
        k += 1
    database["LCSQA_data"].aggregate([
        {"$project":
            {"station": "$nom site",
             "pollutant": "$Pollutant"}},
        {"$group":
            {"_id": "$station",
             "monitored_pollutants":
                {"$push": "$pollutant"}}},
        {"$out": "distribution_pollutants"}
    ])
    database["LCSQA_data"].aggregate([
        {"$group": 
			{"_id": 
				{"station": "$nom site",
				 "pollutant": "$Polluant",
				 "hour": "$hour"},
			 "history":
			 	{"values":
					{"$push": "$valeur brute"},
			 	 "dates":
			 		{"push": "$date"}}}},
		{"$out": "LCSQA_data"}])
	file = "Liste points de mesures 2020 pour site LCSQA_221292021.xlsx"
	data = read_excel(
		file,
		sheet_name=1
	).drop(
		columns=data.columns.tolist()[15:],
		inplace=True
	)
	labels = data.iloc[1].tolist()[:3] + [" "] + data.iloc[1].tolist()[3:-1]
	data.set_axis(
		labels,
		axis="columns",
		copy=False
	).drop(
		[0,1],
		inplace=True
	).drop(
		columns=[" "]
	)
	data["Département"] = data["Code commune"].apply(
        lambda x: french_departments[x[:2]]
    )
	data = data[["Région","Département","Commune","Nom station"]]
    database["LCSQA_stations"].insert_many(
        data.to_dict("records")
    ).aggregate([
        {"$group":
            {"_id": "$Commune",
             "stations": 
                {"city": "$Commune"
                 "names": {"$push": "$Nom station"}},
             "department": "$Département",
             "region": "$Région"}},
        {"$out": "LCSQA_stations"}
    ])
    database["LCSQA_stations"].aggregate([
        {"$group":
            {"_id": "$department",
             "cities": 
                {"department": "$department"
                 "names": {"$push": "$stations"}},
             "region": "$region"}},
        {"$out": "LCSQA_stations"}
    ])
    database["LCSQA_stations"].aggregate([
        {"$group":
            {"_id": "$region",
             "departments":
                {"$push": "$cities"}}},
        {"$out": "LCSQA_stations"}
    ])

def get_values(
	station,
	pollutant,
	n_days):
	data = database["LCSQA_data"].find(
		{"_id.station": station,
		 "_id.pollutant": pollutant}
	)
    dictionary = {str(x): 0 for x in range(24)}
	thresholds = [
        (x/3)*air_pollutants[pollutant][1] 
        for x in range(1,4)
    ]
    for document in data:
		hour = document["_id"]["hour"]
        history = list(zip(
            document["history"]["values"],
            document["history"]["dates"]
        )).reversed()
        i = 0
        while date.today()-history[i][1]<=timedelta(days=n_days):
            i += 1
        dictionary[str(hour)] = mean([e[0] for e in history[:i]])

    fig, ax = pyplot.subplots()
    fig.set_size_inches(17,14)
    yValues = dictionary.values()
    ax.scatter(
        list(map(lambda x: x+"h00"),mean_values.keys()),
        yValues
    )
    highest_mean = max(yValues)
    max_level = 2
    while (max_value > thresholds[max_level]):
        max_level += 1    
    space = (0.40)*thresholds[0]
    lim = thresholds[max_level] if max_level == 2 else max_value
    ax.set_ylim(0,lim+space)
    colors = ["limegreen","yellow","orange","red"]
    y_min = 0     
    for i in list(range(max_level+1)):
        ax.fill_between(
            list(range(24)),
            thresholds[i],
            y2=y_min,
            color=colors[i],
            alpha=0.1
        )
        y_min = thresholds[i]
        if i == 2:
            ax.axhline(
                y=thresholds[i],
                color="blueviolet",
                linestyle="--",
                linewidth=1.7,
                label="Concentration \n moyenne \n"+ \
                      "journalière \n recommandée (O.M.S)"
            )
    if space > 0:
        ax.fill_between(
            list(range(24)),
            ax.get_ylim()[1],
            y2=thresholds[max_level],
            color=colors[max_level+1],
            alpha=0.1
        )
    ax.set_yticks([0])
    ax.set_yticklabels([" "])
    ax.legend(loc="upper right")
    pyplot.gcf().savefig(
        station+"/"+pollutant+"("+str(n_days)+" jours)"
    )
