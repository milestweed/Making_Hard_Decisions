import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'sc_proj.settings')

import django
django.setup()

from sc_app.models import Info, Colors, Closed, Movement, Cbgs, CbgStore


import pandas as pd
bc = pd.read_csv('static/csv/brand_colors.csv')
byStore2018 = pd.read_csv('static/csv/by_store_2018_long.csv')
byStore2019 = pd.read_csv('static/csv/by_store_2019_long.csv')
info = pd.read_csv('static/csv/first_step_data_with_competitors.csv')
targetIDs = pd.read_csv('static/csv/target_ids.csv')
cbgs = pd.read_csv('static/csv/cbgs.csv')
var = pd.read_csv('static/csv/variables.csv')


def populate_colors():

    print("\nPopulating Colors...")
    for i in range(len(bc)):
        b = bc.brands[i]
        c = bc.colors[i]

        Colors.objects.get_or_create(brand=b, hex=c)

    print("Colors Populated\n")

def populate_info():

    print("\nPopulating Info...")
    for i in range(len(info)):
        sgid = info.safegraph_place_id[i]
        ad = info.address[i]
        b = Colors(brand=info.brands[i])
        lat = info.latitude[i]
        lon = info.longitude[i]
        sq_ft = info.area_square_feet[i]
        if info.includes_parking_lot[i] == '1':
            plot = True
        else:
            plot = False
        cat = info.top_category[i]

        Info.objects.get_or_create(sg_id=sgid,
                                address=ad,
                                name=b,
                                lat=lat,
                                lon=lon,
                                sq_ft=sq_ft,
                                p_lot=plot,
                                category=cat)

    print("Info Populated\n")

def populate_closed():

    print("\nPopulating Closed...")
    for i in range(len(targetIDs)):
        name = targetIDs.store_name[i]
        sgid = Info(sg_id=targetIDs.store_id[i])

        Closed.objects.get_or_create(name=name,
                                id=sgid)

    print("Closed Populated\n")

def populate_move(year):

    if year == 2018:

        print("\nPopulating 2018 Movement...")
        for i in range(len(byStore2018)):
            opSt = Info(sg_id = byStore2018.safegraph_place_id[i])
            clSt = Info(sg_id = byStore2018.closed_store[i])
            move = byStore2018.movement[i]

            Movement.objects.get_or_create(open_store=opSt,
                                        closed_store=clSt,
                                        movement=move,
                                        yr=year)

        print("2018 Movement Populated\n")

    if year == 2019:

        print("\nPopulating 2019 Movement...")
        for i in range(len(byStore2019)):
            opSt = Info(sg_id = byStore2019.safegraph_place_id[i])
            clSt = Info(sg_id = byStore2019.closed_store[i])
            move = byStore2019.movement[i]

            Movement.objects.get_or_create(open_store=opSt,
                                        closed_store=clSt,
                                        movement=move,
                                        yr=year)

        print("2019 Movement Populated\n")



def populate_add_cbg_info():

    print("\nPopulating CBG Info...")
    for i in range(len(cbgs)):

        Cbgs.objects.get_or_create(cbgID = cbgs.cbgID[i],
                                    population = cbgs.population[i],
                                    median_income = cbgs.median_income[i])

    print("CBG info Populated\n")

def pop_cbgStore():

    print("\nPopulating CbgStore...")
    for i in range(len(var.iloc[:,0])):

        CbgStore.objects.get_or_create(cbgID = Cbgs(cbgID=var.cbgID[i]),
                                    storeID = Info(sg_id=var.storeID[i]),
                                    percent_visit = var.percent_visits[i],
                                    number_visits = var.number_visits[i],
                                    pop_near_store = var.store_cbg_pop[i],
                                    dist_store_cbg = var.distance_store_cbg[i],
                                    store_area = var.area[i],
                                    p_lot = var.p_lot[i],
                                    poi_near_store = var.poi_count[i],
                                    diversity_near_store = var.poi_diversity[i],
                                    demo_similarity = var.demo_sim[i],
                                    med_inc_near_store = var.med_inc_store_cbg[i],
                                    brand = var.brand[i],
                                    num_visit_brand = var.num_visits_brand[i],
                                    percent_visit_brand = var.per_visits_brand[i],
                                    year = var.year[i])

    print("CbgStore info Populated\n")

if __name__ == "__main__":


    # populate_colors()
    # populate_info()
    # populate_closed()
    # populate_move(2018)
    # populate_move(2019)
    # populate_add_cbg_info()
    pop_cbgStore()
