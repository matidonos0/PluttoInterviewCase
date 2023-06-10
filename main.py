import pandas as pd
import plotly
import json
import random


from flask import Flask, render_template, request
from plotly.graph_objs import Bar, Pie
from risk_classifier import riskyfier


original_file = pd.read_csv('files/setup_file.csv')
original_count = original_file['ID'].nunique()
data = original_file
ids_count = data['ID'].nunique()
companies_count = data[data['Tipo'] == 'Empresa']['ID'].count()
persons_count = data[data['Tipo'] == 'Persona']['ID'].count()

data['risk'] = data.apply(lambda x: riskyfier(x), axis=1)

app = Flask(
	__name__,
	template_folder='templates',
	static_folder='static'
)


@app.route('/')
def test_page():
  company_pct = round(companies_count/ids_count*100,2)
  
  graphs = [
    {
      'data': [
        Bar(
          x = list(data.Tipo.unique()),
          y = list(data['Tipo'].value_counts()),
        )
      ],
      'layout': {
        'title': 'Clients by Type',
        'yaxis': {
          'title': "Count"
        },
        'xaxis': {
          'title': "Type",
          'tickangles': 30
        }
      }
    },
    {
      'data': [
        Pie(
          labels = list(data.risk.unique()),
          values = list(data['risk'].value_counts()),
        )
      ],
      'layout': {
        'title': 'Clients by Type'
      }
    },
    {
      'data': [
        Bar(
          x=list(data.risk.unique()),
          y=list(data['risk'].value_counts())
        )
      ],
      'layout': {
        'title': 'Clients by Type',
        'yaxis': {
          'title': "Count"
        },
        'xaxis': {
          'title': "Type",
          'tickangles': 30
        }
      }
    },
        {
      'data': [
        Bar(
          x=list(data.iloc[:,9].unique()[0:6]),
          y=list(data.iloc[:,9].value_counts()[0:6])
        )
      ],
      'layout': {
        'title': 'Top 5 Clients by Category',
        'yaxis': {
          'title': "Count"
        },
        'xaxis': {
          'title': "Categories",
          'tickangles': 30
        }
      }
    }
  ]
  
  #encode plotly graphs in JSON
  ids = ["graph-{}".format(i) for i, _ in enumerate(graphs)]
  graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

  #render web page with plotly graphs
  return render_template('index.html', 
                         ids=ids, 
                         graphJSON=graphJSON,
                         ids_count = ids_count,
                         company_pct = company_pct
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
    

if __name__ == "__main__":
	app.run(
		# Establishes the host, required for repl to detect the site
    host='0.0.0.0', 
    # Randomly select the port the machine hosts on.
		port=random.randint(2000, 9000)  
	)