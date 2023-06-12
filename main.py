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
rut = list(data.RUT)


app = Flask(
	__name__,
	template_folder='templates',
	static_folder='static'
)


@app.route('/')
def index():
  company_pct = round(companies_count/ids_count*100,2)
  industries = list(data['Industria SII'])
  
  #graph building
  graphs = [
    px.bar(
      data.groupby(['risk','Tipo']).count().reset_index(), x='Tipo', y='ID', color='risk', labels={'ID':'Clients'}, color_discrete_map = {'high_risk': '#F7C0BB', 'medium_risk': '#30BFDD' , 'low_risk': '#7FD4C1'},
      title='Clients by Type and Risk'
    ),
    px.pie(
      data.groupby('Tipo').count().reset_index(), values='ID', names='Tipo', labels={'ID':'Clients'}, title='Client Distribution'
    ),
    px.sunburst(
      data.groupby(['risk','Tipo']).count().reset_index(), path=['Tipo', 'risk'], values='ID', title='Total Portfolio Distribution', labels={'ID':'Clients', 'labels':'Risk', 'parent': 'Tipo Cliente'}
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
  try:
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
  except:
    return render_template('index.html',
                          additional_text = 'Wrong input, please insert a valid one')

@app.route('/industry')
def industry():
  df_risks = data.groupby(['Industria SII', 'risk'])['ID'].count().reset_index().sort_values(by='ID', ascending=False)
  #this gets top risk companies
  df_high_risk = df_risks[df_risks['risk'] == 'high_risk'].head(3)
  df_medium_risk = df_risks[df_risks['risk'] == 'medium_risk'].head(3)
  #this is a filter to be used to get data_X_risk
  high_risk_industries = list(df_high_risk['Industria SII']) 
  medium_risk_industries = list(df_medium_risk['Industria SII'])

  #build risk kpis
  data['boletin'] = data['Tiene B. comercial'] + data['Tiene B. laboral']
  data['debt_late'] = data['Deuda Directa morosa'] + data['Deuda Leasing morosa']
  data['written_off'] = data['Deuda Indirecta castigada'] + data['Deuda Directa castigada']
  
  #this gets KPIs for the indrustries at given risk
  data_medium_risk = data.query('`Industria SII` in @medium_risk_industries').groupby(['Industria SII']).agg(
     avg_debt = ('debt_late', 'mean'),
     avg_boletin = ('boletin', 'mean'),
     avg_legal_causes = ('Causas legales en contra','sum'),
     avg_employees = ('Empleados', 'mean'),
     count = ('ID','count')).round(2)

  data_high_risk = data.query('`Industria SII` in @high_risk_industries').groupby(['Industria SII']).agg(
     avg_wod = ('written_off', 'mean'),
     sum_bankrupt = ('Tiene B. concursal','sum'),
     avg_employees = ('Empleados', 'mean'),
     count = ('ID','count')).round(2)
  data_medium_risk.columns = ['Avg.Written Off Debt', 'Avg.Bulletin Aparitions', 'Avg.Legal Causes Against', 'Avg.Employee Count', 'Clients Count']
  data_high_risk.columns = ['Avg.Written Off Debt', 'Total Concursal Bulletin Aparitions', 'Avg.Employee Count', 'Clients Count']
  
  return render_template(
    'industry.html',
    tables_hr=[data_high_risk.reset_index().to_html(classes='table', header=True, index=False)],
    tables_mr=[data_medium_risk.reset_index().to_html(classes='table',header=True, index=False)]
  ) 

if __name__ == "__main__":
	app.run(
		# Establishes the host, required for repl to detect the site
    host='0.0.0.0', 
    # Randomly select the port the machine hosts on.
		port=random.randint(2000, 9000)  
	)