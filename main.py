import pandas as pd
import plotly
import plotly.express as px
import json
import random


from flask import Flask, render_template, request
from plotly.graph_objs import Bar, Pie
from risk_classifier import riskyfier


original_file = pd.read_csv('files/setup_file.csv')
original_count = original_file['ID'].nunique()
data = original_file
data['risk'] = data.apply(lambda x: riskyfier(x), axis=1)

ids_count = data['ID'].nunique()
companies_count = data[data['Tipo'] == 'Empresa']['ID'].count()
persons_count = data[data['Tipo'] == 'Persona']['ID'].count()
risky_pct = round((data[data['risk'] == 'high_risk']['ID'].nunique()/ids_count)*100,2)


app = Flask(
	__name__,
	template_folder='templates',
	static_folder='static'
)


@app.route('/')
def index():
  company_pct = round(companies_count/ids_count*100,2)
  
  graphs = [
    px.bar(
      data.groupby(['risk','Tipo']).count().reset_index(), x='Tipo', y='ID', color='risk', labels={'ID':'Clients'}, color_discrete_map = {'high_risk': '#F7C0BB', 'medium_risk': '#30BFDD' , 'low_risk': '#7FD4C1'}
    ),
    px.pie(
      data.groupby('Tipo').count().reset_index(), values='ID', names='Tipo'
    ),
    px.sunburst(
      data.groupby(['risk','Tipo']).count().reset_index(), path=['Tipo', 'risk'], values='ID'
    )
  ]
  
  #encode plotly graphs in JSON
  ids = ["graph-{}".format(i) for i, _ in enumerate(graphs)]
  graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

  #render web page with plotly graphs
  return render_template('index.html', 
                         ids=ids, 
                         graphJSON=graphJSON,
                         ids_count = ids_count,
                         company_pct = company_pct,
                         risky_pct = risky_pct
  )


# web page that handles user query and displays model results
@app.route('/detail')
def detail():
  # save user input in query
  query = request.args.get('query', '')
  result = data[data['RUT'] == int(query)]
  return render_template(
    'detail.html',
    query=query,
    result = result,
    name = result['Nombre'],
    risk = result['risk']
  )

@app.route('/industry')
def industy():
  df_risks = data.groupby(['Industria SII', 'risk'])['ID'].count().reset_index().sort_values(by='ID', ascending=False)
  #this gets top risk companies
  df_high_risk = df_risks[df_risks['risk'] == 'high_risk'].head(3)
  df_medium_risk = df_risks[df_risks['risk'] == 'medium_risk'].head(3)
  #this is a filter to be used to get data_X_risk
  high_risk_industries = list(df_high_risk['Industria SII']) 
  medium_risk_industries = list(df_medium_risk['Industria SII'])
  #this gets KPIs for the indrustries at given risk
  data_medium_risk = data.query('`Industria SII` in @medium_risk_industries').groupby(['Industria SII'])[['Deuda Directa castigada', 'Deuda Indirecta castigada', 'Tiene B. concursal']].mean()
  data_high_risk = data.query('`Industria SII` in @high_risk_industries').groupby(['Industria SII'])[['Deuda Directa castigada', 'Deuda Indirecta castigada', 'Tiene B. concursal']].mean()
  return render_template(
    'industry.html',
    hr_industries = high_risk_industries,
    dhr_bankrupty = data_high_risk['Deuda Directa castigada'],
    tables_hr=[data_high_risk.to_html(classes='data', header=True)],
    tables_mr=[data_medium_risk.to_html(classes='data')]
  ) 

if __name__ == "__main__":
	app.run(
		# Establishes the host, required for repl to detect the site
    host='0.0.0.0', 
    # Randomly select the port the machine hosts on.
		port=random.randint(2000, 9000)  
	)