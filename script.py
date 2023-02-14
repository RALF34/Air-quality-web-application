import pandas as pd                                                                                                 
import numpy as np
from matplotlib import pyplot
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.cm import ScalarMappable
from datetime import datetime, date, timedelta

def get_data(station, number_of_days, info_about_stations=False, grouping_necessary=True):
    
    DATE = date.today()
    complete_datasets = []
    dataframes = []
    k = 1
    counter = 0
    while k <= number_of_days :
        DATE -= timedelta(days=k)
        data = pd.read_csv("https://files.data.gouv.fr/lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/"+str(DATE.year)+"/FR_E2_"+DATE.isoformat()+".csv",sep=";")
        if info_about_stations and counter <= 3:
            complete_datasets.append(data)
            counter += 1
        if station in data["code site"].unique().tolist():
            dataframes.append(data[data["code site"]==station])
        k += 1
    ignore_index = False if grouping_necessary else True
    if len(dataframes) >= 1 :
        data = pd.concat(dataframes, ignore_index=ignore_index)
        data = data[data["validité"]==1]
        data["Date"] = data["Date de début"].apply(lambda x: datetime(int(x[:4]),int(x[5:7]),int(x[8:10]),hour=int(x[11:13]),minute=int(x[14:16]),second=int(x[17:])))
        data["Heure"] =  data["Date"].apply(lambda x: x.hour)
        data = data[["Date","Heure","Polluant","valeur brute"]]
        if grouping_necessary:
            gb_pollutant = data.groupby("Polluant")
            data = [(p,gb_pollutant.get_group(p).groupby("Heure").mean()) for p in gb_pollutant.groups.keys()]
            all_the_final_dataframes = []
            for i in range(len(data)):
                polluant, dataframe = data[i][0], data[i][1] 
                dataframe["Polluant"] = pd.Series(data=[polluant]*dataframe.shape[0],index=dataframe.index)
                all_the_final_dataframes.append(dataframe.reset_index(drop=False).set_index("Polluant"))
            results = [pd.concat(all_the_final_dataframes)]
        else:
            results = [data.set_index("Polluant")]
    else:
        if not(grouping_necessary):
            print("Désolé, la station immatriculée " + station + " ne fournit pas assez de données pour réaliser l'analyse demandée.")
            return None
    
    if info_about_stations:
        
        data = pd.read_excel("Liste points de mesures 2020 pour site LCSQA_221292021.xlsx",sheet_name=1)
        data = data.drop(columns=data.columns.tolist()[15:])
        c = data.iloc[1].tolist()[:3] + [" "] + data.iloc[1].tolist()[3:-1]
        data = data.set_axis(c,axis="columns")
        data = data.drop([0,1])
        data = data.drop(columns=[" "])
        data["Département"] = data["Code commune"].apply(lambda x: x[:2])
        data = data.set_index("Code station")[["Secteur de la station","Type ZAS","Région","Département"]]
        results = results + [pd.concat(complete_datasets)] + [data]
    
        
    return results 





colors = {" Niveau\n départemental":"lime", " Niveau\n régional":"green", " Niveau\n national":"gold"}


def variation(A, B):
    C = A < B
    return [100 * ((B[k]-A[k])/A[k] if C[k] else (A[k]-B[k])/B[k]) for k in range(C.size)]

def display_results_with(yValues, creneaux, title=None):
    fig, ax = pyplot.subplots()
    fig.set_size_inches(14,7)
    if title != None:
        pyplot.suptitle(title[0]+" ("+title[1]+")",fontweight="bold",fontsize="x-large")
    ax.axvline()
    line_in_the_middle = False
    x_labels = [yValues[k][0] for k in range(len(yValues))]
    y_values = [yValues[k][1] for k in range(len(yValues))]
    lim = max([abs(k) for k in y_values])
    indexes = []
    
    for k in range(len(y_values)):
        if abs(y_values[k]) == lim:
            indexes.append(k)
    sign_first_value = 0 if y_values[indexes[0]] < 0 else 1
   
    for k in range(len(indexes)):
        sign = 0 if y_values[indexes[k]] < 0 else 1
        if sign_first_value - sign != 0:
            line_in_the_middle = True
    
    if not(line_in_the_middle):
        y_values = y_values + ( [lim] if sign_first_value == 0 else [-lim])
    else:
        y_values = y_values + [0]
        
    ax.axis("off")
    if "Station" in x_labels[0]:
        c = ["cyan"]+[colors[k] for k in x_labels[1:]]
        fontweight = "normal"
    else:
        c = ["cyan"]*len(x_labels)
        fontweight = "bold"
    rects = ax.barh(list(range(len(x_labels)+1)),y_values,color = c + ["white"])
        
    
    for k, rect in enumerate(rects):
        
        if k < len(y_values)-1:
            if rect.get_width() < 0:  
                ax.annotate("+ {:1.1f} % ".format(-rect.get_width()),xy=(rect.get_width(),rect.get_y()+rect.get_height()/2),ha="right",fontsize="x-large")
                ax.text(4,rect.get_y()+rect.get_height()/3,x_labels[k],fontweight=fontweight,fontsize="x-large")
                    
            else: 
                ax.annotate(" + {:1.1f} %".format(rect.get_width()),xy=(rect.get_width(),rect.get_y()+rect.get_height()/2),ha="left",fontsize="x-large")
                ax.text(-4,rect.get_y()+rect.get_height()/3,x_labels[k],ha="right",fontweight=fontweight,fontsize="x-large") 
        
        if k == len(y_values)-1:
            ax.text(-lim/4,rect.get_y()+rect.get_height(),str(creneaux[0][0])+"h00 ---> "+str(creneaux[0][1])+"h00",fontsize="large",fontstretch="expanded",fontweight="bold",bbox=dict(fc="white", boxstyle="round"),ha="right")
            ax.text(lim/4,rect.get_y()+rect.get_height(),str(creneaux[1][0])+"h00 ---> "+str(creneaux[1][1])+"h00",fontsize="large",fontstretch="expanded",fontweight="bold",bbox=dict(fc="white",boxstyle="round"))

guidelines = {
    
"O3" :("ozone",100),
"NO2" :("dioxide d'azote",25),
"SO2" :("dioxide de soufre",40),
"PM2.5" :("particules fines",15),
"PM10" :("particules",45),
"CO" : ("monoxyde de carbone",4),
"NO" :("Oxide d'azote","None"),
"C6H6" :("Benzene","None")}    




def comparative_analysis(station,number_of_days,creneaux):
    
    required_data = get_data(station,number_of_days,info_about_stations=True)
    
    if type(required_data) is list:
        all_the_dataframes = []
        for i in range(len(required_data)-2):
            if type(required_data[i][1]) == pd.core.frame.DataFrame:
                all_the_dataframes.append(required_data[i][1])
        data = pd.concat(all_the_dataframes)
        x_labels = data.index.unique().tolist()
        if "NOX as NO2" in x_labels:
            x_labels = x_labels[:x_labels.index("NOX as NO2")] + x_labels[x_labels.index("NOX as NO2")+1:]
        dataframes = ["first_dataframe","second_dataframe"]
        enough_data = True
        for i in range(2):
            selected_rows = []
            for k in range(creneaux[i][0],creneaux[i][1]+1):
                selected_rows.append(data[data["Heure"]==k])
            if len(selected_rows) != 0:
                dataframes[i] = pd.concat(selected_rows)
            else:
                enough_data = False
        if enough_data:
            available_pollutants = [dataframes[i].groupby(level=0).groups.keys() for i in range(2)]
            xLabels = []
            for p in x_labels:
                if (p in available_pollutants[0] and p in available_pollutants[1]):
                    xLabels.append(p)
            data = [pd.concat([dataframes[i].groupby(level=0).get_group(p).groupby("Heure").mean().mean() for p in xLabels]) for i in range(2)]
            values_to_compare = [data[i].values for i in range(2)]
            variations = variation(*values_to_compare)
            stations = required_data[-1]
            if station not in stations.index.tolist():
                y_values = list(zip(xLabels,variations))
                display_results_with(y_values,creneaux)
                pyplot.gcf().savefig("Results")
                return [station]
            else:
                y_values = [[] for k in range(len(xLabels))]  
                for i in range(len(xLabels)):
                    y_values[i].append([" Station\n "+station,variations[i]])
                type_of_ZAS, type_of_secteur, departement, region = stations.at[station,"Type ZAS"], stations.at[station,"Secteur de la station"], stations.at[station,"Département"], stations.at[station,"Région"]
                grouped_stations = stations.groupby(["Type ZAS","Secteur de la station"])
                  
                if (type_of_ZAS,type_of_secteur) in grouped_stations.groups.keys():
                    set_of_stations = grouped_stations.get_group((type_of_ZAS,type_of_secteur)).index.tolist()
                data = required_data[-2]
                selected_rows = []
                for station in set_of_stations:
                    selected_rows.append(data[data["code site"]==station])
                data = pd.concat(selected_rows) 
                gb_pollutant = data.groupby("Polluant")
                for n, p in enumerate(xLabels):
                    if p in gb_pollutant.groups.keys(): 
                        data_for_p = gb_pollutant.get_group(p).set_index("code site")
                        data_for_p = data_for_p[data_for_p["validité"]==1]
                        data_for_p["Heure"] = data_for_p["Date de début"].apply(lambda x: int(x[11:13]))
                        data_for_p = data_for_p[["Heure","valeur brute"]]
                        list_of_indexes = data_for_p.index.tolist()
                        for k, level in enumerate([" Niveau\n départemental"," Niveau\n régional"," Niveau\n national"]):
                            if k == 0:
                                list_of_stations = stations.groupby("Département").get_group(departement).index.tolist()
                                indexes = []
                                for station in list_of_stations:
                                    if station in list_of_indexes:
                                        indexes.append(station)
                                data = data_for_p.loc[indexes]
                            elif k == 1:
                                list_of_stations = stations.groupby("Région").get_group(region).index.tolist()
                                indexes = []
                                for station in list_of_stations:
                                    if station in list_of_indexes:
                                        indexes.append(station)
                                data = data_for_p.loc[indexes]
                            else:
                                data = data_for_p
                            dataframes = ["first dataframe","second dataframe"]
                            enough_data = True
                            for i in range(2):
                                selected_rows = []
                                for k in range(creneaux[i][0],creneaux[i][1]+1):
                                    selected_rows.append(data[data["Heure"]==k])
         
                                if len(selected_rows) != 0:
                                    dataframes[i] = pd.concat(selected_rows)
                                else:
                                    enough_data = False
                            if enough_data:
                                values_to_compare = [dataframe.groupby("Heure").mean().mean().values for dataframe in dataframes]
                                variations = variation(*values_to_compare) 
                                y_values[n].append([level,variations[0]])
                yValues = []
                polluants = []
                values = []
                for k in range(len(y_values)):
                    if len(y_values[k]) == 1:
                        polluants.append(guidelines[xLabels[k]][0])
                        values.append(y_values[k][0][1]) 
                        y_values[k] = []
                for k in range(len(y_values)):
                    if len(y_values[k]) != 0:
                        yValues.append(((guidelines[xLabels[k]][0].capitalize(),xLabels[k]),y_values[k]))
                yValues.append(list(zip(polluants,values)))
                for k in range(len(yValues)):
                    if k < len(yValues)-1:
                        display_results_with(yValues[k][1],creneaux,title=yValues[k][0])
                        pyplot.gcf().savefig(yValues[k][0][0])
                    else:
                        display_results_with(yValues[k][1],creneaux)
                        pyplot.gcf().savefig("grouped_polluants")
                return [type_of_ZAS,type_of_secteur]

def pollution_levels(station, number_of_days):
    
    required_data = get_data(station,number_of_days,grouping_necessary=False)
    
    if type(data) is list:
        
        pollutants_involved = required_data[0].index.unique().tolist()
        available_pollutants = []    
        for p in ["O3","NO2","SO2","PM2.5","PM10","CO"]:
            if p in pollutants_involved:
                available_pollutants.append(p)
 
        all_the_thresholds = ["e" for i in range(len(available_pollutants))]
        all_registered_values = [[] for i in range(len(available_pollutants))]
        all_y_values = [[[],[]] for i in range(len(available_pollutants))]
        grouped_levels = [[0] for i in range(24)]
        
        data = data[0]
        gb_pollutant = data.groupby(level=0)
    
        for a, p in enumerate(available_pollutants):
            registered_values_for_p = []
            all_the_thresholds[a] = [(x/3)*guidelines[p][1] for x in range(1,4)]
            dataframe = gb_pollutant.get_group(p).reset_index(drop=True)
            nbre_rows = dataframe.shape[0]
            current_sets = [[],[],[]]
 
            for i in range(nbre_rows):
                value = dataframe.at[i,"valeur brute"]
                date = dataframe.at[i,"Date"]
                registered_values_for_p.append((value,date))
                grouped_levels[date.hour].append(value)
                
            all_registered_values[a] = sorted(registered_values_for_p,key=lambda e:e[0])
                
            mean_duration = []
            split_indexes = [0]
            values_for_p, thresholds = all_registered_values[a], all_the_thresholds[a]
            i = 0
            k = 0
            while(i < len(values_for_p) and k < 3):
                if values_for_p[i][0] > thresholds[k]:
                    split_indexes.append(i)
                    k += 1
                i += 1
            split_indexes.append(len(values_for_p))
          
            for i in range(len(split_indexes)-1):
                current_set = sorted(values_for_p[split_indexes[i]:split_indexes[i+1]],key=lambda e:e[1])
                duration = []
                if len(current_set) <= 1:
                    duration.append(len(current_set))
                else:
                    j = 0
                    number_of_consecutive_hours = 0 
                    while j+1<len(current_set):
                        if current_set[j][1] + timedelta(hours=1) == current_set[j+1][1]:
                            number_of_consecutive_hours += 1
                        else:
                            duration.append(number_of_consecutive_hours)
                            number_of_consecutive_hours = 1     
                        j += 1
                    duration.append(number_of_consecutive_hours)
                mean_duration.append(np.mean(np.array(duration)))
            if len(mean_duration) != 4:
                mean_duration += [0]*(4-len(mean_duration))
            
            all_y_values[a][0],all_y_values[a][1] = np.array(mean_duration), [np.mean(np.array(grouped_levels[k])) for k in range(24)]
   
    all_the_norms = [Normalize(vmin=0,vmax=(4/3)*guidelines[p][1],clip=True) for p in available_pollutants]
    
    colors_for_levels = ["limegreen","yellow","orange","red"]
                
    info_about_levels = ["(0 <....< 0,33 x cmjr *)","(niv 1 <....< 0,67 x cmjr)","(niv 2 <....< cmjr)","(niv3 <....)"]
    
    fig, ax = pyplot.subplots()
    fig.set_size_inches(17,14)

    ax.set_facecolor(to_rgba("lightgrey",alpha=0.7))
    ax.set_xlim(-0.4,len(available_pollutants)-0.6)
    ax.set_xticks(list(range(len(available_pollutants))))
    ax.set_xticklabels(available_pollutants)
    ax.set_ylim(0,4)
    ax.set_yticks([1,2,3])
    ax.set_yticklabels(["Minimum","Moyenne","Maximum"])
    grouped_yValues = ["e" for i in range(len(available_pollutants))]
    grouped_hours = ["e" for i in range(len(available_pollutants))]
    for a, p in enumerate(available_pollutants):
        grouped_yValues[a] = (all_registered_values[a][0][0],np.mean(np.array([e[0] for e in all_registered_values[a]])),all_registered_values[a][-1][0])
        grouped_hours[a] = (all_registered_values[a][0][1].hour,all_registered_values[a][-1][1].hour)
    sets_of_yValues = list(zip(*grouped_yValues)) if len(available_pollutants) > 1 else grouped_yValues[0]
    sets_of_hours = list(zip(*grouped_hours)) if len(available_pollutants) > 1 else grouped_hours[0]
    cmap = LinearSegmentedColormap.from_list("mycmap",colors_for_levels)
    for i, values in enumerate(sets_of_yValues):
        if len(available_pollutants) == 1:
            values = [values]
        s = list(zip(all_the_norms,values))
        ax.scatter(list(range(len(available_pollutants))),[i+1]*len(available_pollutants),s=(24*np.ones(len(available_pollutants)))**2,c=[cmap(e[0].__call__(e[1])) for e in s],marker="o",edgecolors="k")
        if i != 1:
            hours = sets_of_hours[0] if i != 2 else sets_of_hours[1] 
            if len(available_pollutants) == 1:
                hours = [hours]
            for k in range(len(available_pollutants)):
                ax.text(k,i+0.85,str(hours[k])+"h00-"+str(hours[k]+1)+"h00",ha="center")
    spaces = [0.17,0.24,0.31,0.4,0.44,0.47]
    for i in range(len(available_pollutants)):
        ax.axvline(i-spaces[i],linestyle="--",color="white")
        ax.axvline(i+spaces[i],linestyle="--",color="white")
    cbar = fig.colorbar(ScalarMappable(cmap=cmap,norm=all_the_norms[a]),ticks=[guidelines[p][1]])
    cbar.ax.set_yticklabels(["\n\n\n\nConcentration \nmoyenne \njournalière \nrecommandée \n(OMS)"])
    pyplot.gcf().savefig("First_plot")
    pyplot.clf()
    for a, p in enumerate(available_pollutants):
        for k in range(2):
            array = np.floor(all_y_values[a][0])
            all_the_hours = [str(int(array[i])) for i in range(array.shape[0])]
            array = np.floor(np.around(60*(all_y_values[a][0]-array)))
            all_the_minutes = [str(int(array[i])) for i in range(array.shape[0])]
            all_the_durations = [" "+all_the_hours[i]+" heure"+("s "if int(all_the_hours[i]) > 1 else " ")+(" " if not(int(all_the_minutes[i])) else ("\n\n et "+all_the_minutes[i]+" minute"+("s "if int(all_the_minutes[i]) > 1 else " ")) if all_the_minutes[i] != 0 else "") for i in range(len(all_the_hours))]
            rects = ax.barh(list(range(5)),[0] + list(all_y_values[0][0]),color=["white"]+colors_for_levels,height=[0.1]+[0.4]*4)
            ax.set_xlim(-1,np.amax(all_y_values[a][0])+1.9)            
            ax.axvline(ymin=0.14)
            array = np.nonzero(all_y_values[a][0])
            spaces_for_xLabels = [-0.71,-0.73,-0.6,-0.41]
            for i, rect in enumerate(rects):
                if i == 0:
                    ax.text(-1,rect.get_y(),"* cmjr = concentration moyenne journalière recommandée (OMS)",fontsize="x-large")
                else:
                    ax.text(spaces_for_xLabels[i-1],rect.get_y()+rect.get_height()/2,"Niveau "+str(i),ha="right",fontweight="bold",fontsize="x-large")
                    ax.text(-0.4,rect.get_y()+rect.get_height()/4,info_about_levels[i-1],ha="right",fontstyle="italic",fontsize="x-large")
                    e = (all_the_durations[i-1],"normal") if np.any(array[0] == i-1) else (" Non atteint ","italic")
                    ax.text(rect.get_width()+(0.4 if all_y_values[a][0][i-1] else 0.1),rect.get_y()+rect.get_height()/2,e[0],va="center",fontstyle=e[1],fontsize="xx-large")
            ax.axis("off")
            pyplot.gcf().savefig(p+"_"+str(k))
            pyplot.clf()
            ax.scatter([str(k)+"h00" for k in range(24)],all_y_values[a][1])
            max_value = np.amax(all_y_values[a][1])
            max_level = 2
            while (max_value > all_the_thresholds[a][max_level]):
                max_level += 1    
            space = (0.40)*all_the_thresholds[a][0]
            lim = all_the_thresholds[a][max_level] if max_level == 2 else max_value
            ax.set_ylim(0,lim+space)
            y_min = 0     
            for i in list(range(max_level+1)):
                ax.fill_between(list(range(24)),all_the_thresholds[a][i],y2=y_min,color=colors_for_levels[i],alpha=0.1)
                y_min = all_the_thresholds[a][i]
                if i == 2:
                    ax.axhline(y=all_the_thresholds[a][i],color="blueviolet",linestyle="--",linewidth=1.7,label=" Concentration \n moyenne \n journalière \n recommandée (O.M.S)")
            if space > 0:
                ax.fill_between(list(range(24)),ax.get_ylim()[1],y2=all_the_thresholds[a][max_level],color=colors_for_levels[max_level+1],alpha=0.1)
            ax.set_yticks([0])
            ax.set_yticklabels([" "])
            ax.legend(loc="upper right")
            pyplot.gcf().savefig(p+"_"+str(k))
            pyplot.clf()






