# # Modules
from flask import Flask, render_template, request, redirect
import requests
import numpy as np
import pandas as pd
import bokeh
from bokeh.plotting import figure
from bokeh.io import show
from bokeh.embed import components
from datetime import datetime
bv = bokeh.__version__


# # Flask app

app = Flask(__name__)
app.vars={}
feat = ['Open','Close','Range']


@app.route('/')
def main():
	return redirect('/index')


@app.route('/index',methods=['GET','POST'])
def index():
	if request.method == 'GET':
		return render_template('index.html')
	else:
		#request was a POST
		app.vars['ticker'] = request.form['ticker'].upper()
		app.vars['start_year'] = request.form['year']
		try: 
			int(app.vars['start_year'])
			ticker = app.vars['ticker']
			start_year = app.vars['start_year']
			app.vars['tag'] = f'Data specified for {ticker} in {start_year}'
		except ValueError:
			app.vars['start_year'] = ''
			app.vars['tag'] = 'Start year not specified/recognized'
		app.vars['select'] = [feat[q] for q in range(3) if feat[q] in request.form.values()]
		return redirect('/graph')


@app.route('/graph',methods=['GET','POST'])
def graph():
	
	# Request data from Quandl and get into pandas collapsing data by week
	req = 'https://www.quandl.com/api/v3/datasets/WIKI/'
	req = '%s%s.json?api_key=F1hKMg5xhSpoPqV6zULD&collapse=weekly' % (req,app.vars['ticker'])
	if not app.vars['start_year']=='':
		req = '%s&start_date=%s-01-01' % (req,app.vars['start_year'])
	r = requests.get(req)
	cols = r.json()['dataset']['column_names'][0:5]
	df = pd.DataFrame(np.array(r.json()['dataset']['data'])[:,0:5],columns=cols)
	df.Date = pd.to_datetime(df.Date)
	df[['Open','High','Low','Close']] = df[['Open','High','Low','Close']].astype(float)
	if not app.vars['start_year']=='':
		if df.Date.iloc[-1].year>int(app.vars['start_year']):
			app.vars['tag'] = '%s, but Quandl record begins in %s' % (app.vars['tag'],df.Date.iloc[-1].year)
	now = datetime.now()
	current_time = now.strftime("%m/%d/%Y ")
	tag = app.vars['tag']
	if 'Generated' not in app.vars['tag']:
		app.vars['tag'] = f'{tag}. Generated on {current_time}'

	app.vars['desc'] = r.json()['dataset']['name'].split(',')[0]
	
	
	# Make Bokeh plot and insert using components
	# ------------------- ------------------------|
	p = figure(plot_width=550, plot_height=550, title=app.vars['ticker'], x_axis_type="datetime")
	if 'Range' in app.vars['select']:
		tmpx = np.array([df.Date,df.Date[::-1]]).flatten()
		tmpy = np.array([df.High,df.Low[::-1]]).flatten()
		p.patch(tmpx, tmpy, alpha=0.3, color="green",legend='Range (High/Low)')
	if 'Open' in app.vars['select']:
		p.line(df.Date, df.Open, line_width=2,legend='Opening price')
	if 'Close' in app.vars['select']:
		p.line(df.Date, df.Close, line_width=2, line_color="#FB8072",legend='Closing price')
	p.legend.orientation = "vertical"
		
	# axis labels
	p.xaxis.axis_label = "Time"
	p.xaxis.axis_label_text_font_style = 'bold'
	p.xaxis.axis_label_text_font_size = '14pt'
	p.xaxis.major_label_orientation = np.pi/4
	p.xaxis.major_label_text_font_size = '14pt'
	p.xaxis.bounds = (df.Date.iloc[-1],df.Date.iloc[0])
	p.yaxis.axis_label = "Price"
	p.yaxis.axis_label_text_font_style = 'bold'
	p.yaxis.axis_label_text_font_size = '14pt'
	p.yaxis.major_label_text_font_size = '14pt'

	
	# render graph template
	# ------------------- ------------------------|
	script, div = components(p)
	return render_template('graph.html', bv=bv, ticker=app.vars['ticker'],
							ttag=app.vars['desc'], yrtag=app.vars['tag'],
							script=script, div=div)
		
	
@app.errorhandler(500)
def error_handler(e):
	return render_template('error.html',ticker=app.vars['ticker'],year=app.vars['start_year'])

# # If main
if __name__ == '__main__':
  app.run(port=5000,debug=False)
