from django.shortcuts import render
from django.db import connection
from . import forms
from sc_app.models import Closed, Colors, Movement, Info, Cbgs, CbgStore
import plotly.graph_objs as go
from plotly.offline import plot
import json
import pandas as pd
from plotly.subplots import make_subplots
from sc_proj.config import *

colors = pd.read_csv('static/csv/brand_colors.csv',index_col=0)
colorDict = {x:y for x,y in zip(colors.brands, colors.colors)}

###############################
##         INDEX VIEW         ##
###############################

# Create your views here.
def index(request):
    return render(request, 'sc_app/index.html')


























###############################
##     TOPSTORES VIEW        ##
###############################


def topStores(request):
    form = forms.YearSelect()

    ###############################
    ##    Generate base plot     ##
    ###############################
    mapbox_access_token = get_mb_token()
    MB_style = 'mapbox://styles/mapbox/streets-v11'
    plot_divs = []
    table_dicts = []

    for store in ['T07','T06','T11']:
        year = 2018
        store = Closed.objects.filter(name=store)
        store_name = [str(x.name) for x in store][0]
        store = [str(x.id) for x in store][0]


        qs = Movement.objects.select_related().filter(closed_store=store, yr=year)
        q = qs.values('open_store', 'movement')
        closed = pd.DataFrame.from_records(q)

        closed = closed.rename(columns={'open_store':'sg_id'})
        closed.set_index('sg_id', inplace=True)
        closed = closed.drop(index=store)
        mv_min = closed['movement'].min()
        mv_max = closed['movement'].max()
        mv_range = mv_max-mv_min
        closed['norm'] = closed['movement'].apply(lambda x: 5+((x - mv_min)*(100-5))/mv_range)


        query = Info.objects.filter(sg_id = store)

        center = [(x.lat, x.lon) for x in query][0]

        fig = go.Figure()

        cols = Colors.objects.all()
        for col in cols:

            color = str(col.hex)
            brand = str(col.brand)

            qs = Info.objects.filter(name = brand)
            q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
            df = pd.DataFrame.from_records(q)
            closed = closed.rename(columns={'open_store':'sg_id'})
            df.set_index('sg_id', inplace=True)
            plot_df = df.join(closed, on='sg_id',how='left')
            plot_df['movement'] = plot_df['movement'].astype(str)
            plot_df['sq_ft'] = plot_df['sq_ft'].astype(str)
            plot_df['p_lot'] = plot_df['p_lot'].astype(str)
            plot_df.dropna(inplace=True)

            fig.add_trace(go.Scattermapbox(
                                lat = plot_df.lat,
                                lon = plot_df.lon,
                                mode = 'markers',
                                marker = go.scattermapbox.Marker(
                                            size=plot_df.norm,
                                            color=color,
                                            opacity=0.6
                                ),
                                name = brand,
                                hovertemplate = '<b>'+ brand + '</b><br><br>'
                                                '<b>Additional Traffic: </b><br>' + plot_df.movement + '<br>' +
                                                '<b>Address: </b><br>' + plot_df.address + '<br>' +
                                                '<b>Category: </b><br>' + plot_df.category + '<br>' +
                                                '<b>Square Footage: </b><br>' + plot_df.sq_ft + '<br>' +
                                                '<b>Has Parking Lot: </b><br>' + plot_df.p_lot + '<br>' +
                                                "<extra></extra>"


                            ))

        qs = Info.objects.select_related().filter(sg_id=store)
        q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
        ct_info = pd.DataFrame.from_records(q)
        ct_info['sq_ft'] = ct_info['sq_ft'].astype(str)
        ct_info['p_lot'] = ct_info['p_lot'].astype(str)

        fig.add_trace(go.Scattermapbox(
                            lat = [center[0]],
                            lon = [center[1]],
                            mode = 'markers',
                            marker=go.scattermapbox.Marker(
                                        size = 10,
                                        color = '#000000',
                                        opacity = 1
                            ),
                            name = 'Target '+store_name+' **closed**',
                            hovertemplate = '<b>Target '+store_name+' **closed**</b><br><br>'
                                            '<b>Address: </b><br>' + ct_info.address + '<br>' +
                                            '<b>Category: </b><br>' + ct_info.category + '<br>' +
                                            '<b>Square Footage: </b><br>' + ct_info.sq_ft + '<br>' +
                                            '<b>Has Parking Lot: </b><br>' + ct_info.p_lot + '<br>' +
                                            "<extra></extra>"
        ))

        fig.update_layout(
            autosize=False,
            hovermode='closest',
            showlegend=False,
            margin=dict(
                l=0,
                r=0,
                t=30,
                b=20),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=center[0],
                    lon=center[1]),
                pitch=60,
                zoom=10),
            title = "Resulting Movement After Closing Store " + store_name,
            height=500,
            width=500
        )


        qs = Info.objects.exclude(sg_id=store)
        q = qs.values('sg_id','name','address','lat','lon','category','sq_ft','p_lot')
        df = pd.DataFrame.from_records(q)
        df.set_index('sg_id', inplace=True)

        tdf = df.join(closed)
        top_tdf = tdf.sort_values(by='movement', ascending=False).head(5)
        table_dicts.append([{'brand':top_tdf.loc[i,'name'],
                        'address':top_tdf.loc[i,'address'],
                        'sq_ft':top_tdf.loc[i,'sq_ft'],
                        'move':round(top_tdf.loc[i,'movement'])} for i in list(top_tdf.index)])


        plot_divs.append(plot(fig, output_type='div', include_plotlyjs=False))


    ###############################
    ##  Generate plot from input ##
    ###############################

    if request.method == 'POST':
        form = forms.YearSelect(request.POST)

        if form.is_valid():

            ###############################
            ##   Bubble plot of movement ##
            ###############################
            for store in ['T07','T11','T06']:

                year = form.cleaned_data['year']
                store = Closed.objects.filter(name=store)
                store_name = [str(x.name) for x in store][0]
                store = [str(x.id) for x in store][0]


                qs = Movement.objects.select_related().filter(closed_store=store, yr=year)
                q = qs.values('open_store', 'movement')
                closed = pd.DataFrame.from_records(q)

                closed = closed.rename(columns={'open_store':'sg_id'})
                closed.set_index('sg_id', inplace=True)
                closed = closed.drop(index=store)
                mv_min = closed['movement'].min()
                mv_max = closed['movement'].max()
                mv_range = mv_max-mv_min
                closed['norm'] = closed['movement'].apply(lambda x: 5+((x - mv_min)*(100-5))/mv_range)


                query = Info.objects.filter(sg_id = store)

                center = [(x.lat, x.lon) for x in query][0]

                fig = go.Figure()

                cols = Colors.objects.all()
                for col in cols:

                    color = str(col.hex)
                    brand = str(col.brand)

                    qs = Info.objects.filter(name = brand)
                    q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
                    df = pd.DataFrame.from_records(q)
                    closed = closed.rename(columns={'open_store':'sg_id'})
                    df.set_index('sg_id', inplace=True)
                    plot_df = df.join(closed, on='sg_id',how='left')
                    plot_df['movement'] = plot_df['movement'].astype(str)
                    plot_df['sq_ft'] = plot_df['sq_ft'].astype(str)
                    plot_df['p_lot'] = plot_df['p_lot'].astype(str)
                    plot_df.dropna(inplace=True)

                    fig.add_trace(go.Scattermapbox(
                                        lat = plot_df.lat,
                                        lon = plot_df.lon,
                                        mode = 'markers',
                                        marker = go.scattermapbox.Marker(
                                                    size=plot_df.norm,
                                                    color=color,
                                                    opacity=0.6
                                        ),
                                        name = brand,
                                        hovertemplate = '<b>'+ brand + '</b><br><br>'
                                                        '<b>Additional Traffic: </b><br>' + plot_df.movement + '<br>' +
                                                        '<b>Address: </b><br>' + plot_df.address + '<br>' +
                                                        '<b>Category: </b><br>' + plot_df.category + '<br>' +
                                                        '<b>Square Footage: </b><br>' + plot_df.sq_ft + '<br>' +
                                                        '<b>Has Parking Lot: </b><br>' + plot_df.p_lot + '<br>' +
                                                        "<extra></extra>"


                                    ))

                qs = Info.objects.select_related().filter(sg_id=store)
                q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
                ct_info = pd.DataFrame.from_records(q)
                ct_info['sq_ft'] = ct_info['sq_ft'].astype(str)
                ct_info['p_lot'] = ct_info['p_lot'].astype(str)

                fig.add_trace(go.Scattermapbox(
                                    lat = [center[0]],
                                    lon = [center[1]],
                                    mode = 'markers',
                                    marker=go.scattermapbox.Marker(
                                                size = 10,
                                                color = '#000000',
                                                opacity = 1
                                    ),
                                    name = 'Target '+store_name+' **closed**',
                                    hovertemplate = '<b>Target '+store_name+' **closed**</b><br><br>'
                                                    '<b>Address: </b><br>' + ct_info.address + '<br>' +
                                                    '<b>Category: </b><br>' + ct_info.category + '<br>' +
                                                    '<b>Square Footage: </b><br>' + ct_info.sq_ft + '<br>' +
                                                    '<b>Has Parking Lot: </b><br>' + ct_info.p_lot + '<br>' +
                                                    "<extra></extra>"
                ))

                fig.update_layout(
                    autosize=False,
                    hovermode='closest',
                    mapbox=dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        center=dict(
                            lat=center[0],
                            lon=center[1]),
                        pitch=60,
                        zoom=12),
                    title = "Resulting Movement After Closing Store " + store_name,
                    height=800,
                    width=1200
                )

                plot_div = plot(fig, output_type='div', include_plotlyjs=False)

            qs = Info.objects.exclude(sg_id=store)
            q = qs.values('sg_id','name','address','lat','lon','category','sq_ft','p_lot')
            df = pd.DataFrame.from_records(q)
            df.set_index('sg_id', inplace=True)

            tdf = df.join(closed)
            top_tdf = tdf.sort_values(by='movement', ascending=False).head(5)
            table_dicts.append([{'brand':top_tdf.loc[i,'name'],
                            'address':top_tdf.loc[i,'address'],
                            'sq_ft':top_tdf.loc[i,'sq_ft'],
                            'move':round(top_tdf.loc[i,'movement'],2)} for i in list(top_tdf.index)])





    return render(request, 'sc_app/topStores.html', context={'form':form,
                                                            'store_plot1':plot_divs[0],
                                                            'store_plot2':plot_divs[1],
                                                            'store_plot3':plot_divs[2],
                                                            'tbl1':table_dicts[0],
                                                            'tbl2':table_dicts[1],
                                                            'tbl3':table_dicts[2],
                                                            'store1':'T07',
                                                            'store2':'T11',
                                                            'store3':'T06',})


























###############################
##         DATA VIEW         ##
###############################


def data(request):

    ###############################
    ## Generate form for sidebar ##
    ###############################

    form = forms.CloseStore()
    nyCbg = json.load(open('static/json/nyc_cbgs.json'))
    for feat in nyCbg['features']:
        feat['id'] = feat['properties']['GEOID']




    ###############################
    ##    Generate base plots    ##
    ##      Bubble Plot          ##
    ###############################
    tblDict = None
    map_div = None
    bar_div = None
    inp = None
    mapbox_access_token = get_mb_token()
    MB_style = 'mapbox://styles/mapbox/streets-v11'


    #####################
    #   Targets plot    #
    #####################

    color = Colors.objects.filter(brand = "Target").values().get()['hex']
    brand = "Target"

    targets = pd.DataFrame.from_records(Closed.objects.all().values())
    targets = targets.rename(columns={"id_id":"sg_id"}).set_index("sg_id")

    qs = Info.objects.filter(name = "Target")
    q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
    df = pd.DataFrame.from_records(q)
    df['sq_ft'] = df['sq_ft'].astype(str)
    df['p_lot'] = df['p_lot'].astype(str)
    df = df.set_index("sg_id").join(targets).reset_index()


    fig = go.Figure(go.Scattermapbox(
                        lat = df.lat,
                        lon = df.lon,
                        mode = 'markers',
                        marker = go.scattermapbox.Marker(
                                    color=color,
                                    size=25,
                                    opacity=0.6
                        ),
                        hovertemplate = '<b>'+ brand + ' ' + df.name + '</b><br><br>' +
                                        '<b>Address: </b><br>' + df.address + '<br>' +
                                        '<b>Category: </b><br>' + df.category + '<br>' +
                                        '<b>Square Footage: </b><br>' + df.sq_ft + '<br>' +
                                        '<b>Has Parking Lot: </b><br>' + df.p_lot + '<br>' +
                                        "<extra></extra>"))

    fig.update_layout(
        autosize=False,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=40.713056,
                lon=-73.95444),
            pitch=0,
            zoom=10),
        title = "<b>Target Stores</b>",
        height=800,
        width=1200,
        margin = {'t':50,'r':0,'l':0,'b':20}
    )

    targets_div = plot(fig, output_type='div', include_plotlyjs=False)

    ####################
    # Competitors plot #
    ####################
    cols = Colors.objects.exclude(brand = "Target")
    fig = go.Figure()

    for col in cols:

        color = str(col.hex)
        brand = str(col.brand)

        qs = Info.objects.filter(name = brand)
        q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
        df = pd.DataFrame.from_records(q)
        df['sq_ft'] = df['sq_ft'].astype(str)
        df['p_lot'] = df['p_lot'].astype(str)

        fig.add_trace(go.Scattermapbox(
                            lat = df.lat,
                            lon = df.lon,
                            mode = 'markers',
                            marker = go.scattermapbox.Marker(
                                        color=color,
                                        size=15,
                                        opacity=0.6
                            ),
                            name = brand,
                            hovertemplate = '<b>'+ brand + '</b><br><br>'
                                            '<b>Address: </b><br>' + df.address + '<br>' +
                                            '<b>Category: </b><br>' + df.category + '<br>' +
                                            '<b>Square Footage: </b><br>' + df.sq_ft + '<br>' +
                                            '<b>Has Parking Lot: </b><br>' + df.p_lot + '<br>' +
                                            "<extra></extra>"))

        fig.update_layout(
            autosize=False,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=40.713056,
                    lon=-74.013333),
                pitch=0,
                zoom=10),
            width = 600,
            height = 700,
            title = "<b>Target Competitors</b>",
            margin = {'t':30,'r':0,'l':0,'b':20}
        )

        comp_div = plot(fig, output_type='div', include_plotlyjs=False)

    ###############################
    ##        Choropleth         ##
    ###############################

    qs = Cbgs.objects.all()
    q = qs.values()
    choro_df = pd.DataFrame.from_records(q)


    fig = go.Figure(go.Choroplethmapbox(geojson=nyCbg,
                            locations=choro_df.cbgID,
                            z=choro_df.median_income,
                            colorscale="Viridis",
                            name = "Median Income",
                            marker_opacity=0.5,
                            marker_line_width=0,
                            colorbar = dict(title = "<b>Median Household<br>Income</b>")))

    fig.add_trace(go.Choroplethmapbox(geojson=nyCbg,
                            locations=choro_df.cbgID,
                            z=choro_df.population,
                            colorscale="Viridis",
                            name = "Population",
                            visible = False,
                            marker_opacity=0.5,
                            marker_line_width=0,
                            colorbar = dict(title = "<b>Population</b>")))


    fig.update_layout(
        updatemenus=[
            dict(x=1,
                 y=1,
                 active = 0,
                 buttons = list([
                            dict(label = "Median Income",
                                method = "update",
                                args=[{"visible":[True,False]}]),
                            dict(label = "Population",
                                method = "update",
                                args = [{"visible":[False,True]}])
                 ]))],
        autosize=False,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=40.713056,
                lon=-74.013333),
            pitch=0,
            zoom=10),
        width = 600,
        height = 700,
        title = "<b>Census Block Groups</b>",
        margin = {'t':30,'r':0,'l':0,'b':20}
    )

    choro_div = plot(fig, output_type='div', include_plotlyjs=False)



    ###############################
    ##  Generate plot from input ##
    ###############################

    if request.method == 'POST':
        form = forms.CloseStore(request.POST)

        if form.is_valid():

            inp = True
            type = form.cleaned_data['type']
            year = form.cleaned_data['year']
            q = Closed.objects.filter(name=form.cleaned_data['store']).values().get()
            store_name = q['name']
            store = q['id_id']

            query = Info.objects.filter(sg_id = store).values().get()
            center = [query['lat'],query['lon']]

            qs = Info.objects.select_related().filter(sg_id=store)
            q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
            ct_info = pd.DataFrame.from_records(q)
            ct_info['sq_ft'] = ct_info['sq_ft'].astype(str)
            ct_info['p_lot'] = ct_info['p_lot'].astype(str)


            if type == 'foot':

                ###############################
                ##   Bubble plot of movement ##
                ###############################


                qs = Movement.objects.select_related().filter(closed_store=store, yr=year)
                q = qs.values('open_store', 'movement')
                closed = pd.DataFrame.from_records(q)

                closed = closed.rename(columns={'open_store':'sg_id'})
                closed.set_index('sg_id', inplace=True)
                closed = closed.drop(index=store)
                mv_min = closed['movement'].min()
                mv_max = closed['movement'].max()
                mv_range = mv_max-mv_min
                closed['norm'] = closed['movement'].apply(lambda x: 5+((x - mv_min)*(100-5))/mv_range)


                mapbox_access_token = open("static/.mapbox_token").read()
                MB_style = 'mapbox://styles/mapbox/streets-v11'
                fig = go.Figure()

                cols = Colors.objects.all()
                for col in cols:

                    color = str(col.hex)
                    brand = str(col.brand)

                    qs = Info.objects.filter(name = brand)
                    q = qs.values('sg_id','address','lat','lon','category','sq_ft','p_lot')
                    df = pd.DataFrame.from_records(q)
                    closed = closed.rename(columns={'open_store':'sg_id'})
                    df.set_index('sg_id', inplace=True)
                    plot_df = df.join(closed, on='sg_id',how='left')
                    plot_df['movement'] = plot_df['movement'].astype(str)
                    plot_df['sq_ft'] = plot_df['sq_ft'].astype(str)
                    plot_df['p_lot'] = plot_df['p_lot'].astype(str)
                    plot_df.dropna(inplace=True)

                    fig.add_trace(go.Scattermapbox(
                                        lat = plot_df.lat,
                                        lon = plot_df.lon,
                                        mode = 'markers',
                                        marker = go.scattermapbox.Marker(
                                                    size=plot_df.norm,
                                                    color=color,
                                                    opacity=0.6
                                        ),
                                        name = brand,
                                        hovertemplate = '<b>'+ brand + '</b><br><br>'
                                                        '<b>Additional Traffic: </b><br>' + plot_df.movement + '<br>' +
                                                        '<b>Address: </b><br>' + plot_df.address + '<br>' +
                                                        '<b>Category: </b><br>' + plot_df.category + '<br>' +
                                                        '<b>Square Footage: </b><br>' + plot_df.sq_ft + '<br>' +
                                                        '<b>Has Parking Lot: </b><br>' + plot_df.p_lot + '<br>' +
                                                        "<extra></extra>"


                                    ))

                fig.add_trace(go.Scattermapbox(
                                    lat = [center[0]],
                                    lon = [center[1]],
                                    mode = 'markers',
                                    marker=go.scattermapbox.Marker(
                                                size = 10,
                                                color = '#000000',
                                                opacity = 1
                                    ),
                                    name = 'Target '+store_name+' **closed**',
                                    hovertemplate = '<b>Target '+store_name+' **closed**</b><br><br>'
                                                    '<b>Address: </b><br>' + ct_info.address + '<br>' +
                                                    '<b>Category: </b><br>' + ct_info.category + '<br>' +
                                                    '<b>Square Footage: </b><br>' + ct_info.sq_ft + '<br>' +
                                                    '<b>Has Parking Lot: </b><br>' + ct_info.p_lot + '<br>' +
                                                    "<extra></extra>"
                ))

                fig.update_layout(
                    autosize=False,
                    hovermode='closest',
                    mapbox=dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        center=dict(
                            lat=center[0],
                            lon=center[1]),
                        pitch=60,
                        zoom=10),
                    title = "<b>Resulting Movement After Closing Store " + store_name + "</b>",
                    height=800,
                    width=600,
                    margin = {'t':30,'r':0,'l':0,'b':30}
                )

                map_div = plot(fig, output_type='div', include_plotlyjs=False)

                ###############################
                ##       Store Barplot       ##
                ###############################

                with connection.cursor() as cursor:
                    query = cursor.execute("""
                                            SELECT i.sg_id, i.address, i.sq_ft, i.p_lot, i.category, i.name_id, m.movement
                                            FROM sc_app_Info AS i, sc_app_movement  AS m
                                            WHERE m.closed_store_id = %s
                                            AND m.yr = %s
                                            AND m.closed_store_id != m.open_store_id
                                            AND i.sg_id = m.open_store_id
                                            ORDER BY m.movement DESC
                                            """, [store, year])
                    top5stores = pd.DataFrame.from_records(query.fetchall()).head(5)
                    top5stores.rename(columns={0:'safegraph_place_id', 1:'address',2:'area_square_feet',3:'includes_parking_lot',4:'category',5:'brands',6:'movement'}, inplace=True)

                top5stores['txt'] = ['Competitor 1','Competitor 2','Competitor 3','Competitor 4','Competitor 5']


                with connection.cursor() as cursor:
                    params = list(top5stores.safegraph_place_id)
                    params.append(year)
                    query = cursor.execute("""
                                            SELECT storeID_id, MAX(poi_near_store), MAX(diversity_near_store)
                                            FROM sc_app_CbgStore
                                            WHERE storeID_id IN (%s, %s, %s, %s, %s)
                                            AND year = %s
                                            GROUP BY storeID_id
                                            """, params)
                    other = pd.DataFrame.from_records(query.fetchall())
                    other.rename(columns={0:"safegraph_place_id", 1:'poi_count',2:'poi_diversity'}, inplace=True)

                # print(other.head())
                # other = variables[(variables.storeID.str.contains("|".join(list(top5stores.safegraph_place_id)))) & (variables.year == 2018)]\
                #         .groupby('storeID').max().loc[:,['poi_count','poi_diversity']]
                other.set_index('safegraph_place_id',  inplace=True)
                top5stores = top5stores.set_index('safegraph_place_id').join(other, how='left')
                top5stores.reset_index(inplace=True)
                top5stores['colors'] = top5stores.brands.apply(lambda x: colorDict[x])


                fig = make_subplots(
                    rows=4, cols=1,
                    vertical_spacing=0.05,
                    specs=[[{"type": "bar"}],
                           [{"type": "bar"}],
                           [{"type": "bar"}],
                           [{"type": "bar"}]])

                fig.add_trace(go.Bar(x = top5stores.txt,
                                     y = top5stores.movement,
                                     marker=dict(color=top5stores.colors),
                                     showlegend=False,
                                     hovertemplate = "<b>Brand: </b>" + top5stores.brands + "<br>" +
                                                     "<b>Store ID: </b>" + top5stores.safegraph_place_id + '<br>' +
                                                     "<b>Address: </b>" + top5stores.address + '<br>' +
                                                     "<b>Includes Parking Lot: </b>" + top5stores.includes_parking_lot.astype(str) +
                                                     "<extra></extra>"),
                              row = 1,
                              col = 1)

                fig.add_trace(go.Bar(x = top5stores.txt,
                                     y = top5stores.poi_count,
                                     marker=dict(color=top5stores.colors),
                                     showlegend=False,
                                     hovertemplate = "<b>Brand: </b>" + top5stores.brands + "<br>" +
                                                     "<b>Store ID: </b>" + top5stores.safegraph_place_id + '<br>' +
                                                     "<b>Address: </b>" + top5stores.address + '<br>' +
                                                     "<b>Includes Parking Lot: </b>" + top5stores.includes_parking_lot.astype(str) +
                                                     "<extra></extra>"),
                              row = 2,
                              col = 1)
                fig.add_trace(go.Bar(x = top5stores.txt,
                                     y = top5stores.area_square_feet,
                                     marker=dict(color=top5stores.colors),
                                     showlegend=False,
                                     hovertemplate = "<b>Brand: </b>" + top5stores.brands + "<br>" +
                                                     "<b>Store ID: </b>" + top5stores.safegraph_place_id + '<br>' +
                                                     "<b>Address: </b>" + top5stores.address + '<br>' +
                                                     "<b>Includes Parking Lot: </b>" + top5stores.includes_parking_lot.astype(str) +
                                                     "<extra></extra>"),
                              row = 3,
                              col = 1)
                fig.add_trace(go.Bar(x = top5stores.txt,
                                     y = top5stores.poi_diversity,
                                     marker=dict(color=top5stores.colors),
                                     showlegend=False,
                                     hovertemplate = "<b>Brand: </b>" + top5stores.brands + "<br>" +
                                                     "<b>Store ID: </b>" + top5stores.safegraph_place_id + '<br>' +
                                                     "<b>Address: </b>" + top5stores.address + '<br>' +
                                                     "<b>Includes Parking Lot: </b>" + top5stores.includes_parking_lot.astype(str) +
                                                     "<extra></extra>"),
                              row = 4,
                              col = 1)




                fig.update_xaxes(showticklabels=False, row=1,col=1)
                fig.update_xaxes(showticklabels=False, row=2,col=1)
                fig.update_xaxes(showticklabels=False, row=3,col=1)
                fig.update_xaxes(tickangle=45, row=4,col=1)
                fig.update_yaxes(title_text='Additional Traffic', row = 1, col=1)
                fig.update_yaxes(title_text='Places of Interest', row = 2, col=1)
                fig.update_yaxes(title_text='Square Foot', row = 3, col=1)
                fig.update_yaxes(title_text='Diversity', row = 4, col=1)

                fig.update_layout(
                    width=400,
                    height=800,
                    margin=dict(r=0, t=35, b=10, l=0),
                    title = dict(text = "Top 5 Benefactors"),
                    annotations=[
                        dict(
                            text="<b>Additional Traffic</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=1.03),
                        dict(
                            text="<b>Number of POIs Near Store</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.77),
                        dict(
                            text="<b>Area of Store</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5),
                        dict(
                            text="<b>POI Diversity Near Store</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.22)
                    ]
                )

                bar_div = plot(fig, output_type='div', include_plotlyjs=False)

                ###############################
                ##        Info Table         ##
                ###############################

                qs = Info.objects.exclude(sg_id=store)
                q = qs.values('sg_id','name','address','lat','lon','category','sq_ft','p_lot')
                df = pd.DataFrame.from_records(q)
                df.set_index('sg_id', inplace=True)

                tdf = df.join(closed)
                top_tdf = tdf.sort_values(by='movement', ascending=False).head(5)
                tblDict = [{'brand':top_tdf.loc[i,'name'],
                            'category':top_tdf.loc[i,'category'],
                            'address':top_tdf.loc[i,'address'],
                            'sq_ft':top_tdf.loc[i,'sq_ft'],
                            'move':round(top_tdf.loc[i,'movement'],2)} for i in list(top_tdf.index)]

            if type == "cbg":
                ###############################
                ##        Choropleth         ##
                ###############################

                qs = CbgStore.objects.filter(storeID = store, number_visits__gt=0, year=year)
                q = qs.values('cbgID', 'number_visits')
                choro_df = pd.DataFrame.from_records(q)

                fig = go.Figure(go.Choroplethmapbox(geojson=nyCbg,
                                        locations=choro_df.cbgID,
                                        z=choro_df.number_visits,
                                        colorscale="Viridis",
                                        marker_opacity=0.5,
                                        marker_line_width=0,
                                        colorbar = dict(title = "<b>Number of<br>Visits</b>")))

                fig.add_trace(go.Scattermapbox(
                                    lat = [center[0]],
                                    lon = [center[1]],
                                    mode = 'markers',
                                    marker=go.scattermapbox.Marker(
                                                size = 10,
                                                color = '#000000',
                                                opacity = 1
                                    ),
                                    name = 'Target '+store_name+' **closed**',
                                    hovertemplate = '<b>Target '+store_name+' **closed**</b><br><br>'
                                                    '<b>Address: </b><br>' + ct_info.address + '<br>' +
                                                    '<b>Category: </b><br>' + ct_info.category + '<br>' +
                                                    '<b>Square Footage: </b><br>' + ct_info.sq_ft + '<br>' +
                                                    '<b>Has Parking Lot: </b><br>' + ct_info.p_lot + '<br>' +
                                                    "<extra></extra>"
                ))


                fig.update_layout(
                        autosize=False,
                        hovermode='closest',
                        mapbox=dict(
                            accesstoken=mapbox_access_token,
                            bearing=0,
                            center=dict(
                                lat=center[0],
                                lon=center[1]),
                            pitch=20,
                            zoom=11),
                        title=dict(text="<b>Number of Visits per CBG in " + str(year) + "</b>"),
                        height=800,
                        width=600,
                        margin = {'t':30,'r':0,'l':0,'b':0}
                )
                config = {'displayModeBar':False}
                # fig.update_layout(mapbox_style="carto-positron",
                #                   mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})
                # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

                map_div = plot(fig, output_type='div', include_plotlyjs=False)


                ###############################
                ##        CBG Barplot        ##
                ###############################

                with connection.cursor() as cursor:
                    query = cursor.execute("""
                                            SELECT i.sg_id, i.address, i.sq_ft, i.p_lot, i.category, i.name_id, m.movement
                                            FROM sc_app_Info AS i, sc_app_movement  AS m
                                            WHERE m.closed_store_id = %s
                                            AND m.yr = %s
                                            AND m.closed_store_id != m.open_store_id
                                            AND i.sg_id = m.open_store_id
                                            ORDER BY m.movement DESC
                                            """, [store, year])
                    top5stores = pd.DataFrame.from_records(query.fetchall()).head(5)
                    top5stores.rename(columns={0:'safegraph_place_id', 1:'address',2:'area_square_feet',3:'includes_parking_lot',4:'category',5:'brands',6:'movement'}, inplace=True)

                top5stores['txt'] = ['Competitor 1','Competitor 2','Competitor 3','Competitor 4','Competitor 5']
                print(top5stores.columns)

                qs = CbgStore.objects.filter(year=year, storeID=store)
                top5cbg = qs.order_by('-number_visits')\
                            .values("cbgID", "number_visits", "percent_visit_brand", "dist_store_cbg", "demo_similarity")[0:5]
                top5cbg = pd.DataFrame.from_records(top5cbg)

                cbgs = pd.DataFrame.from_records(Cbgs.objects.all().values())
                top5cbg = top5cbg.set_index('cbgID').join(cbgs.set_index('cbgID'), how = 'left')
                top5cbg.reset_index(inplace=True)
                top5cbg.cbgID = top5cbg.cbgID.astype(str)
                top5cbg['txt'] = ['Top CBG 1','Top CBG 2',' Top CBG 3','Top CBG 4','Top CBG 5']

                fig = make_subplots(
                    rows=4, cols=1,
                    vertical_spacing=0.05,
                    specs=[[{"type": "bar"}],
                           [{"type": "bar"}],
                           [{"type": "bar"}],
                           [{"type": "bar"}]])

                fig.add_trace(go.Bar(x = top5cbg.txt,
                                     y = top5cbg.number_visits,
                                     marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                                     showlegend=False,
                                     hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                                     "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                                     "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                                     "<extra></extra>"),
                              row = 1,
                              col = 1)

                fig.add_trace(go.Bar(x = top5cbg.txt,
                                     y = top5cbg.percent_visit_brand,
                                     marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                                     showlegend=False,
                                     hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                                     "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                                     "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                                     "<extra></extra>"),
                              row = 2,
                              col = 1)

                fig.add_trace(go.Bar(x = top5cbg.txt,
                                     y = top5cbg.dist_store_cbg,
                                     marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                                     showlegend=False,
                                     hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                                     "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                                     "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                                     "<extra></extra>"),
                              row = 3,
                              col = 1)

                fig.add_trace(go.Bar(x = top5cbg.txt,
                                     y = top5cbg.demo_similarity,
                                     marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                                     showlegend=False,
                                     hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                                     "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                                     "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                                     "<extra></extra>"),
                              row = 4,
                              col = 1)

                fig.update_xaxes(showticklabels=False, row=1,col=1)
                fig.update_xaxes(showticklabels=False, row=2,col=1)
                fig.update_xaxes(showticklabels=False, row=3,col=1)
                fig.update_xaxes(tickangle=45, row=4,col=1)
                fig.update_yaxes(title_text='Number of visits', row = 1, col=1)
                fig.update_yaxes(title_text='Percent', range=(0,1), row = 2, col=1)
                fig.update_yaxes(title_text='Distance (haversine)', row = 3, col=1)
                fig.update_yaxes(title_text='Demographic Similarity', range=(0,1), row = 4, col=1)

                fig.update_layout(
                    width=400,
                    height=800,
                    margin=dict(r=0, t=35, b=0, l=0),
                    title = dict(text = "Top 5 CBG Comparison"),
                    annotations=[
                        dict(
                            text="<b>Number of Visits From CBG</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=1.03),
                        dict(
                            text="<b>Percent Visits to Brand</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.77),
                        dict(
                            text="<b>Distance to Store from CBG</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5),
                        dict(
                            text="<b>Demographic Similarity</b>",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.22)
                    ]
                )

                bar_div = plot(fig, output_type='div', include_plotlyjs=False)



                tblDict = [{'brand':top5stores.loc[i,'brands'],
                            'category':top5stores.loc[i,'category'],
                            'address':top5stores.loc[i,'address'],
                            'sq_ft':top5stores.loc[i,'area_square_feet'],
                            'move':round(top5stores.loc[i,'movement'],2)} for i in list(top5stores.index)]

    ###############################
    ##        Render page        ##
    ###############################


    return render(request, 'sc_app/data.html', context={'form':form,
                                                        'input': inp,
                                                        'targets_plot':targets_div,
                                                        'comp_plot':comp_div,
                                                        'choro_plot':choro_div,
                                                        'map_plot':map_div,
                                                        'bar_plot':bar_div,
                                                        'tbl':tblDict})




###############################
##        PAPER VIEW         ##
###############################

def paper(request):
    return render(request, 'sc_app/paper.html')



###############################
##       PEOPLE VIEW         ##
###############################

def people(request):
    return render(request, 'sc_app/people.html')


###############################
##        TEST VIEW          ##
###############################

def test(request):
    qs = CbgStore.objects.filter(storeID="sg:e2543bebe82742a1941c21660d9f4168").filter(num_visit_18__gt=0)
    print(qs)
    q = qs.values()
    df = pd.DataFrame.from_records(q)
    print(df.head())


    return render(request, 'sc_app/data3.html')
