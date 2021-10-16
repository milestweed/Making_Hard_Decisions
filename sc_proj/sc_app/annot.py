
# Import for testing
import plotly.express as px
import plotly.graph_objs as go
from plotly.offline import plot
import json
import pandas as pd
from plotly.subplots import make_subplots

# long form data for 2018 and 2019 each store connected to one closed store
long2018 = pd.read_csv('../static/csv/long_format_2018.csv', index_col=0)
long2019 = pd.read_csv('../static/csv/long_format_2019.csv', index_col=0)

# each store's connection to each CBG (This takes a long time to load!)
variables = pd.read_csv('../static/csv/variables.csv', index_col=0)

# CBG id numbers, pop, med_income
cbgs = pd.read_csv('../static/csv/cbgs.csv', index_col=0)

# Hexidecimal colors connected to each brand name
colors = pd.read_csv('../static/csv/brand_colors.csv',index_col=0)

# Turns the above into a dictionary *Prob unnecessary*
colorDict = {x:y for x,y in zip(colors.brands, colors.colors)}

#This creates a closstore form object which has a drop down for year and one for store number
#form = forms.CloseStore()

# This is a JSON of the cbg geometries
nyCbg = json.load(open('../static/json/nyc_cbgs.json'))
# it needs to be altered so that the id is the GEOID
for feat in nyCbg['features']:
    feat['id'] = feat['properties']['GEOID']



###############################
##    Generate base plots    ##
##      Bubble Plot          ##
###############################

# Initialize an object that will contain a dictionary of values for an html table
tblDict = None

# will contain the store info bar charts
stBar_div = None

# will contain the CBG info bar charts
cbgBar_div = None

# mapbox access token for the bubble plots
mapbox_access_token = open("../static/.mapbox_token").read()

# Mapbox map style
MB_style = 'mapbox://styles/mapbox/streets-v11'

# Initialize a base figure
fig = go.Figure()

# queries all of the object from the Colors table (brand,Hexidecimal)
cols = Colors.objects.all()

# for each brand/hex combo in the cols object...
for col in cols:

    # set color to the Hexidecimal string
    color = str(col.hex)

    # set brand to the brand name string
    brand = str(col.brand)

    # Queries the info table for every store of the brand (returns a list of relations objects)
    # specifies the desired values from each record
    qs = Info.objects.filter(name = brand).values('sg_id','address','lat','lon','category','sq_ft','p_lot')

    # Creates a dataframe from the records
    df = pd.DataFrame.from_records(q)

    # Converts sq_ft and p_lot to strings because they are only used in hover labels
    df['sq_ft'] = df['sq_ft'].astype(str)
    df['p_lot'] = df['p_lot'].astype(str)

    # Add a trace for every store of each brand
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
                                        "<extra></extra>"


                    ))

# Overall Layout format for bubble plot
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
    title = "<b>All Places Of Interest</b>",
    height=600,
    width=1000,
    margin = {'t':30,'r':0,'l':0,'b':20}
)

# crates an HTML div stringfor displaying the plot
plot_div = plot(fig, output_type='div', include_plotlyjs=False)





###############################
##        Choropleth         ##
###############################

# Creates a query set of every CBG with id and med_income
qs = Cbgs.objects.all().values('cbgID', 'median_income')

# Turns the qs into DF
choro_df = pd.DataFrame.from_records(qs)

# Uses the GeoJSON to map all CBG which are colored by Income (would like to add population)
fig = go.Figure(go.Choroplethmapbox(geojson=nyCbg,
                        locations=choro_df.cbgID,
                        z=choro_df.median_income,
                        colorscale="Viridis",
                        marker_opacity=0.5,
                        marker_line_width=0,
                        colorbar = dict(title = "<b>Median Household<br>Income</b>")))


# Overall layout for choropleth
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
        title=dict(text="<b>Median Income by CBG</b>"),
        height=600,
        width=1000,
        margin = {'t':30,'r':0,'l':0,'b':0}
)
config = {'displayModeBar':False}
# fig.update_layout(mapbox_style="carto-positron",
#                   mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# create Div for choropleth
choro_div = plot(fig, output_type='div', include_plotlyjs=False)



###############################
##  Generate plot from input ##
###############################

# Checks to see if the request methhod is POST i.e. the form was entered
if request.method == 'POST':

    # sets the form object to contain the posted data
    form = forms.CloseStore(request.POST)

    # checks that the form is valid
    if form.is_valid():

        ###############################
        ##   Bubble plot of movement ##
        ###############################

        # collect the year from the form object
        year = form.cleaned_data['year']

        # Collect the store name and safeGraph id
        q = Closed.objects.filter(name=form.cleaned_data['store']).values().get()
        store_name = q['name']
        store = q['id_id']

        # collect records of movement from particular year where the specified store has been closed
        qs = Movement.objects.select_related().filter(closed_store=store, yr=year)
        q = qs.values('open_store', 'movement')

        # Create a dataframe of records
        closed = pd.DataFrame.from_records(q)

        # Rename column open_store -> sg_id
        closed = closed.rename(columns={'open_store':'sg_id'})
        closed.set_index('sg_id', inplace=True)
        closed = closed.drop(index=store)

        # Normalize movement for better bubble size
        mv_min = closed['movement'].min()
        mv_max = closed['movement'].max()
        mv_range = mv_max-mv_min
        closed['norm'] = closed['movement'].apply(lambda x: 5+((x - mv_min)*(100-5))/mv_range)

        # Query for the closed store and get the lat and lon to center the map
        query = Info.objects.filter(sg_id = store).values().get()
        center = [query['lat'],query['lon']]

        # Import the mapbox access token
        mapbox_access_token = open("static/.mapbox_token").read()
        MB_style = 'mapbox://styles/mapbox/streets-v11'

        # create a new figure
        fig = go.Figure()

        # collect all of the brands/colors
        cols = Colors.objects.all()

        #For each brand
        for col in cols:

            #set color to the Hexidecimal and brand to the brand name
            color = str(col.hex)
            brand = str(col.brand)

            # query the Info tablel where the name = brand and collect the data requires
            qs = Info.objects.filter(name = brand).values('sg_id','address','lat','lon','category','sq_ft','p_lot')

            #Turn it into a dataframe
            df = pd.DataFrame.from_records(qs)

            # Redundant?
            closed = closed.rename(columns={'open_store':'sg_id'})
            df.set_index('sg_id', inplace=True)

            # Left join of closed onto df so only stores of the same brand in closed are joined
            plot_df = df.join(closed, on='sg_id',how='left')

            # Convert field the appear in the hover text to strings
            plot_df['movement'] = plot_df['movement'].astype(str)
            plot_df['sq_ft'] = plot_df['sq_ft'].astype(str)
            plot_df['p_lot'] = plot_df['p_lot'].astype(str)

            # Drop and rows with missing information
            plot_df.dropna(inplace=True)

            # Add a trace of all stores for the specific brand
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

        #Query the info for the closed store
        qs = Info.objects.select_related().filter(sg_id=store).values('sg_id','address','lat','lon','category','sq_ft','p_lot')

        # Records as dataframe
        ct_info = pd.DataFrame.from_records(qs)

        # Change type of hover info
        ct_info['sq_ft'] = ct_info['sq_ft'].astype(str)
        ct_info['p_lot'] = ct_info['p_lot'].astype(str)

        # Add a trace for the closed store
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


        # Update the layout for the final bubble plot
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
            height=600,
            width=1000,
            margin = {'t':30,'r':0,'l':0,'b':30}
        )

        plot_div = plot(fig, output_type='div', include_plotlyjs=False)

        ###############################
        ##       Store Barplot       ##
        ###############################
        if year == 2018:
            top5stores = long2018[(long2018['closed-store']==store)]\
                        .sort_values('movement', ascending=False)\
                        .loc[:,['safegraph_place_id', 'area_square_feet', 'brands', 'top_category',
                               'address', 'includes_parking_lot','movement']]\
                        .head(5)
        else:
            top5stores = long2019[(long2019['closed-store']==store)]\
                        .sort_values('movement', ascending=False)\
                        .loc[:,['safegraph_place_id', 'area_square_feet', 'brands', 'top_category',
                               'address', 'includes_parking_lot','movement']]\
                        .head(5)
        top5stores.includes_parking_lot = top5stores.includes_parking_lot.apply(lambda x: True if x == 1 else False)
        top5stores['txt'] = ['Competitor 1','Competitor 2','Competitor 3','Competitor 4','Competitor 5']
        other = variables[(variables.storeID.str.contains("|".join(list(top5stores.safegraph_place_id)))) & (variables.year == 2018)]\
                .groupby('storeID').max().loc[:,['poi_count','poi_diversity']]
        top5stores = top5stores.set_index('safegraph_place_id').join(other, how='left')
        top5stores.reset_index(inplace=True)
        top5stores['colors'] = top5stores.brands.apply(lambda x: colorDict[x])



        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.5, 0.5],
            vertical_spacing=0.25,
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [ {"type": "bar"}, {"type": "bar"}]])

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
                      row = 1,
                      col = 2)
        fig.add_trace(go.Bar(x = top5stores.txt,
                             y = top5stores.area_square_feet,
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
                             y = top5stores.poi_diversity,
                             marker=dict(color=top5stores.colors),
                             showlegend=False,
                             hovertemplate = "<b>Brand: </b>" + top5stores.brands + "<br>" +
                                             "<b>Store ID: </b>" + top5stores.safegraph_place_id + '<br>' +
                                             "<b>Address: </b>" + top5stores.address + '<br>' +
                                             "<b>Includes Parking Lot: </b>" + top5stores.includes_parking_lot.astype(str) +
                                             "<extra></extra>"),
                      row = 2,
                      col = 2)




        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text='Additional Traffic', row = 1, col=1)
        fig.update_yaxes(title_text='Places of Interest', row = 1, col=2)
        fig.update_yaxes(title_text='Square Foot', row = 2, col=1)
        fig.update_yaxes(title_text='Diversity', row = 2, col=2)

        fig.update_layout(
            margin=dict(r=10, t=30, b=50, l=60),
            title = dict(text = "2018: Top 5 Benefactors From Closing Target T13"),
            annotations=[
                dict(
                    text="<b>Additional Traffic</b>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=0.65),
                dict(
                    text="<b>POI Diversity Near Store</b>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.7,
                    y=0),
                dict(
                    text="<b>Number of POIs Near Store</b>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.7,
                    y=0.65),
                dict(
                    text="<b>Area of Store</b>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=0)
            ]
        )

        stBar_div = plot(fig, output_type='div', include_plotlyjs=False)

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
                    pitch=60,
                    zoom=10),
                title=dict(text="<b>Number of Visits per CBG in " + str(year) + "</b>"),
                height=600,
                width=1000,
                margin = {'t':30,'r':0,'l':0,'b':0}
        )
        config = {'displayModeBar':False}
        # fig.update_layout(mapbox_style="carto-positron",
        #                   mapbox_zoom=3, mapbox_center = {"lat": 37.0902, "lon": -95.7129})
        # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        choro_div = plot(fig, output_type='div', include_plotlyjs=False)


        ###############################
        ##        CBG Barplot        ##
        ###############################

        # collect the top 5 cbg for where storeID is the closed store for a particular year
        top5cbg = variables[(variables['storeID']==store) & (variables['year']==int(year))]\
                .sort_values('number_visits', ascending=False)\
                .loc[:,['cbgID', 'number_visits', 'per_visits_brand', 'distance_store_cbg', 'demo_sim']]\
                .head(5)

        # Join with the CBG info on the CBGID
        top5cbg = top5cbg.set_index('cbgID').join(cbgs.set_index('cbgID'), how = 'left')
        top5cbg.reset_index(inplace=True)

        # Set ID as string
        top5cbg.cbgID = top5cbg.cbgID.astype(str)

        # CBG Name for plots
        top5cbg['txt'] = ['Top CBG 1','Top CBG 2',' Top CBG 3','Top CBG 4','Top CBG 5']

        # set up a figure as subplots
        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.5, 0.5],
            row_heights=[0.5, 0.5],
            vertical_spacing=0.2,
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [ {"type": "bar"}, {"type": "bar"}]])

        # Add a trace for number of visits
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

        # Add a trace for percent of CBG visits to brand
        fig.add_trace(go.Bar(x = top5cbg.txt,
                             y = top5cbg.per_visits_brand,
                             marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                             showlegend=False,
                             hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                             "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                             "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                             "<extra></extra>"),
                      row = 2,
                      col = 1)

        # Add a trace for distance to store from cbg
        fig.add_trace(go.Bar(x = top5cbg.txt,
                             y = top5cbg.distance_store_cbg,
                             marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                             showlegend=False,
                             hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                             "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                             "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                             "<extra></extra>"),
                      row = 1,
                      col = 2)

        # Add a trace for demographic similarity between cbg and store location
        fig.add_trace(go.Bar(x = top5cbg.txt,
                             y = top5cbg.demo_sim,
                             marker=dict(color=["#264653",'#2A9D8F','#E9C46A','#F4A261','#E76F51']),
                             showlegend=False,
                             hovertemplate = "<b>CBG ID: </b>" + top5cbg.cbgID + '<br>' +
                                             "<b>Population: </b>" + top5cbg.population.astype(str) + '<br>' +
                                             "<b>Median Income: </b>" + top5cbg.median_income.astype(str) +
                                             "<extra></extra>"),
                      row = 2,
                      col = 2)

        # Adjust axis labels as necessary
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text='Number of visits', row = 1, col=1)
        fig.update_yaxes(title_text='Percent', range=(0,1), row = 2, col=1)
        fig.update_yaxes(title_text='Distance (haversine)', row = 1, col=2)
        fig.update_yaxes(title_text='Demographic Similarity', range=(0,1), row = 2, col=2)

        # update overall layout
        fig.update_layout(
            margin=dict(r=10, t=25, b=40, l=60),
            title = dict(text = "2018: Top 5 CBG Comparison For Target T13"),
            # annotations=[
            #     dict(
            #         text="<b>Number of Visits</b>",
            #         showarrow=False,
            #         xref="paper",
            #         yref="paper",
            #         x=0,
            #         y=0.64),
            #     dict(
            #         text="<b>Percent Visits to Brand</b>",
            #         showarrow=False,
            #         xref="paper",
            #         yref="paper",
            #         x=0,
            #         y=0),
            #     dict(
            #         text="<b>Distance to Store from CBG</b>",
            #         showarrow=False,
            #         xref="paper",
            #         yref="paper",
            #         x=0.64,
            #         y=0.64),
            #     dict(
            #         text="<b>Demographic Similarity</b>",
            #         showarrow=False,
            #         xref="paper",
            #         yref="paper",
            #         x=0.63,
            #         y=0,)
            # ]
        )

        cbgBar_div = plot(fig, output_type='div', include_plotlyjs=False)
###############################
##        Render page        ##
###############################


return render(request, 'sc_app/data.html', context={'form':form,
                                                    'store_plot':plot_div,
                                                    'tbl':tblDict,
                                                    'choro_plot':choro_div,
                                                    'store_bar':stBar_div,
                                                    'cbg_bar':cbgBar_div})
