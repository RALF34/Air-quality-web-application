names = [
    "Ain",
    "Aisne",
    "Allier",
    "Alpes-de-Haute-Provence",
    "Hautes-Alpes",
    "Alpes-Maritimes",
    "Ardèche",
    "Ardennes",
    "Ariège",
    "Aube",
    "Aveyron",
    "Bouches-du-Rhône",
    "Calvados",
    "Cantal",
    "Charente",
    "Charente-Maritime",
    "Cher",
    "Corrèze",
    "Corse-du-Sud",
   "Haute-Corse",
   "Côte-d'Or",
   "Côtes d'Armor",
   "Creuse",
   "Dordogne",
   "Doubs",
   "Drôme",
   "Eure",
   "Eure-et-Loir",
   "Finistère",
   "Gard",
   "Haute-Garonne",
   "Gers",
   "Gironde",
   "Hérault",
   "Ille-et-Vilaine",
   "Indre",
   "Indre-et-Loire",
   "Isère",
   "Jura",
   "Landes",
   "Loir-et-Cher",
   "Loire",
   "Haute-Loire",
   "Loire-Atlantique",
   "Loiret",
   "Lot",
   "Lot-et-Garonne",
   "Lozère",
   "Maine-et-Loire",
   "Manche",
   "Marne",
   "Haute-Marne",
   "Mayenne",
   "Meurthe-et-Moselle",
   "Meuse",
   "Morbilhan",
   "Moselle,
   "Nièvre",
   "Nord",
   "Oise",
   "Orne",
   "Pas-de-Calais",
   "Puy-de-Dôme",
   "Pyrénées-Atlantiques",
   "Hautes-Pyrénées",
   "Pyrénées-Orientales",
   "Bas-Rhin",
   "Haut-Rhin",
   "Rhône",
   "Saône",
   "Saône-et-Loire",
   "Sarthe",
   "Savoie",
   "Haute-Savoie",
   "Paris",
   "Seine-Maritime",
   "Seine-et-Marne",
   "Yvelines",
   "Deux-Sèvres",
   "Somme",
   "Tarn",
   "Tarn-et-Garonne",
   "Var",
   "Vaucluse",
   "Vendée",
   "Vienne",
   "Haute-Vienne",
   "Vosges",
   "Yonne",
   "Territoire de Belfort",
   "Essonne",
   "Hauts-de-Seine",
   "Seine-Saint-Denis",
   "Val-de-Marne",
   "Val-d'Oise",
   "Guadeloupe",
   "Martinique",
   "Guyane",
   "La Réunion",
   "Mayotte"
]

french_departments = {
    code: name for code, name in zip(
        list(range(1,11)+list(range(12,98)),
        names)
    )
}

air_pollutants = {
   "O3": ("Ozone",100),
   "NO2": ("Dioxyde d'azote",25),
   "SO2": ("Dioxyde de soufre",40),
   "PM2.5": ("Particules fines",15),
   "PM10": ("Particules",45),
   "CO": ("Monoxyde de carbone",4)
}