from django.shortcuts import render
from .models import Pollutant, Station, UserRequest, StatisticData
from .script import comparative_analysis, pollution_levels



def home(request):
    return render(request, "myApp/home.html") 




main_titles = ["Répartition du temps passé à différents niveaux de pollution","Durées moyennes de temps passé à différents niveaux de pollution","Variation journalière moyenne de la pollution"]
info_about_pollutants = { "PM" : ("Les matières particulaires sont un indicateur indirect courant de la pollution de l'air. Elles \n" + \
                                 "affectent plus de personnes que n'importe quel autre polluant. Les principaux composants en sont \n" + \
                                 "les sulfates, les nitrates, l'ammoniac, le chlorure de sodium, le carbone noir, la poussière d'un \n" + \
                                 "mélange complexe de particules solides et liquides de substances organiques et minérales en \n" + \
                                 "suspension dans l'air. Si  les particules d'un diamètre n'excédant pas 10 microns (PM10) peuvent \n" + \
                                 "pénétrer et se loger profondémént à l'intérieur des poumons, celles dont le diamètre est inférieure \n" + \
                                 "ou égal à 2,5 microns (PM2.5) sont encore plus nocives pour la santé. Ces dernières peuvent franchir \n" + \
                                 "la barrière pulmonaire et entrer dans la circulation sanguine. \n" + \
                                 "L'exposition chronique aux particules contribue au risque de développer des maladies cardiovasculaires \n" + \
                                 "et respiratoires, et des cancers pulmonaires.",
                                 "Il existe une relation étroite et quantitative entre l'exposition à des concentrations élevées de \n" + \
                                 "particules et de particules fines (PM10 et PM2.5) et l'augmentation de la mortalité et de la morbidité, \n" + \
                                 "au quotidien comme à plus long terme. Inversement, lorsque les concentrations de particules et de \n" + \
                                 "particules fines sont réduites, la mortalité associée baisse (en supposant que les autres facteurs \n" + \
                                 "restent inchangés). Ce constat permet aux décideurs de projeter les effets bénéfiques pour la santé de \n" + \
                                 "la population d'une réduction de la pollution atmosphérique particulaire. \n" + \
                                 "Même à faibles concentrations, les particules polluantes ont des répercussions sur la santé ; aucun \n" + \
                                 "seuil n'a été identifié au-dessous duquel elles n'affectent pas la santé. C'est pourquoi les limites \n" + \
                                 "préconisées dans les lignes directrices modiales de l'OMS visent parvenir à des concentrations de \n" + \
                                 "particules les plus faibles possibles."),
                        "O3" : ("L'ozone au niveau du sol - à ne pas confondre avec la couche d'ozone dans la haute atmosphère - est l'un \n" + \
                                 "des principaux constituants du smog photochimique, brouillard urbain formé par la réaction avec le \n" + \
                                "rayonnement solaire de divers polluants, comme les oxydes d'azote (NOx), émis par les véhicules et \n" + \
                                "l'industrie, et les composés organiques volatiles (COV) émis par les véhicules, les solvants et l'industrie.",
                                "Présent à des concentrations trop élevées, l'ozone a des effets marqués sur la santé humaine. Il peut causer \n" + \
                                "des problème respiratoire, le déclenchement de crises d'asthme, une diminution de la fonction pulmonaire et \n" + \
                                "des maladies respiratoires."),
                        "NO2" : ("Le NO2 est la principale source d'aéorosols de nitrate, qui représentent une proportion importante des PM2.5 \n" + \
                                "et, en présence de rayons ultraviolets, d'ozone. Les émissions anthropiques de NO2 proviennent principalement \n" + \
                                "de la combustion (chauffage, production d'éléctricité, moteurs des véhicules automobiles et des bateaux.",
                                "Les études épidémiologiques ont montré que les symptômes bronchitiques chez l'enfant asthmatique augmentent \n" + \
                                "avec une exposition de longue durée au NO2. Les concentrations de NO2 actuellement mesurées (ou observées) \n" + \
                                "dans les villes d'Europe et d'Amérique du Nord sont également associées à une diminution du développement \n" + \
                                "de la fonction pulmonaire."),
                        "SO2" : ("Le SO2 est un gaz incolore, d'odeur piquante. Il est produit par la combustion d'énergies fossiles \n" + \
                                "(charbon et pétrole) et la fonte de minerais contenant du soufre. La principale source anthropique \n" + \
                                "de SO2 est la combustion d'énergies fossiles contenant du soufre pour le chauffage domestique, la \n" + \
                                "production d'électricité ou les véhicules à moteur.",
                                "Le SO2 affecte le système respiratoire et le fonctionnement des poumons, et il provoque une irritation \n" + \
                                "des yeux. L'inflammation des voies respiratoires entraîne de la toux, une production de mucus, une \n" + \
                                "exacerbatation de l'asthme, des bronchites chroniques et une sensibilisation aux infections des voies \n" + \
                                "respiratoires. Le nombre des admissions à l'hopital pour des cardiopathies et la mortalité augmentent \n" + \
                                "les jours de fortes concentrations de SO2"),
                        "CO" :  ("Gaz inodore, incolore et inflammable, le monoxyde de carbone se forme lors de la combustion incomplète \n" + \
                                "de matières organiques (gaz, charbon, fioul, bois). Sa source principale est le trafic automobile.",
                                "Le monoxyde de carbone se fixe à la place de l'oxygène sur l'hémoglobine du sang,entraînant un manque \n" + \
                                "d'oxygénation de l'organisme (coeur, cerveau, etc.). Les premiers symptômes sont des maux de tête et des \n" + \
                                "vertiges. Ces symptômes s'aggravent avec l'augmentation de la concentration de monoxyde de carbone. \n" + \
                                "(nausées, vomissements) et peuvent, en cas d'exposition prolongée, aller jusqu'au coma ou à la mort.")
                        }

def results(request):
    
    station = request.POST.get("station")
    number_of_days = request.POST.get("number_of_days")
    if number_of_days == 0:
        start_1 = request.POST.get("start_1")
        end_1 = request.POST.get("end_1")
        start_2 = request.POST.get("start_2")
        end_2 = request.POST.get("end_2")
        
    r, request_created = UserRequest.objects.get_or_create(number_of_days=number_of_days, first_interval=start_1+" - "+end_1, second_interval=start_2+" - "+end_2)
    if request_created:
        parameters = list(number_of_days) if number_of_days != 0 else list((int(start_1),int(end_1)),(int(start_2),int(end_2)))
        type_of_zone, data_about_pollutants = comparative_analysis(station,*parameters) if number_of_days != 0 else pollution_levels(station,*parameters)
        s, station_created = Station.objects.get_or_create(name=station,defaults={"type_of_zone":type_of_zone})
        involved_pollutants = [e[0] for e in data_about_pollutants]
        if station_created:    
            for e in involved_pollutants:
                p = Pollutant.objects.get_or_create(name=e[0],symbol=e[1])
                s.pollutants.add(p)
        r.station = s
        position = 1
        for i_0, element in enumerate(data_about_pollutants):
            p = Pollutant.objects.get(symbol=element[0])
            for i_1, g in enumerate(element[1]):
                stat = StatisticData.objects.create(about=p,associated_with=r,position=position,graph=g)
                if  number_of_days != 0 and i_1 == 0:
                    stat.display_main_title = True
                    stat.main_title = main_titles[i_0]
                position += 1
    all_the_statistics = r.statistic_data.all()
    context = {"user_request" : r, "all_the_statistics" : all_the_statistics}
    return render(request, "myApp/results.html", context) 