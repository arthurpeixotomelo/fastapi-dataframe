from os import listdir
from os.path import join, dirname, abspath

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

plants_dict = {
    'excaulebur': {
        'nome': 'Excalibur',
        'especie': 'Dracaena Trifasciata',
        'temp': {'min': 21.6, 'max': 29.1},
        'umid': {'min': 48, 'max': 75},
        'signal': {'min': -1.0, 'max': 0.82421875},
    },
    'totosa': {
        'nome': 'Totosa',
        'especie': 'Portulacaria Afra',
        'temp': {'min': 24.7, 'max': 28.7},
        'umid': {'min': 60, 'max': 75},
        'signal': {'min': -1.0, 'max': 95.7734375},
    }
}

def get_plant_data(plant, limit=None):
    with open(join(dirname(abspath(__file__)), 'data', f'{plant.title()}.csv'), 'r') as f:
        df = pd.read_csv(f, nrows=limit)
        return df.sort_values(by=['Data', 'Hora'])

def get_file_data(file, plant):
    if file.split('_')[0] == plant.title():
        with open(join(dirname(abspath(__file__)), 'data', file), 'r') as f:
            df = pd.read_csv(f)
            df['Data'] = pd.to_datetime(file.split('.')[0][-10:], format='%Y-%m-%d', yearfirst=True)
            df['Data'] = df[['Data', 'Hora']].apply(
                lambda x: x[0] + pd.DateOffset(1) if str(x[1]) >= str('00:00:00') 
                and str(x[1]) < str('06:00:00') else x[0], axis=1
            )
            return df[['Valor do sinal', 'Temperatura', 'Umidade', 'Data', 'Hora']]
        
def concat_plant_data(plant):
    df = pd.concat([get_file_data(file, plant) for file in listdir(join(dirname(abspath(__file__)), 'data'))])
    return df.sort_values(by=['Data', 'Hora']).to_csv(f'./data/{plant.title()}.csv', index=False)

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='templates')

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.get('/plants/{plant}/info', response_class=HTMLResponse)
async def get_info(plant):
    df = get_plant_data(plant, limit=5000)
    df['Temperatura'] = df['Temperatura'].apply(lambda x: float(x[:4]))
    df['Umidade'] = df['Umidade'].apply(lambda x: int(x[:2]))
    return f'''
        <section id='info'>
            <h3>Informações da planta</h3>
            <div>
                <button href='/plants/{plant}/graph' hx-get='/plants/{plant}/graph' hx-target='#content' hx-trigger='click' hx-swap='outerHTML' hx-indicator='#info'>
                    Carregar Gráfico
                </button>
                <button href='/plants/{plant}/table' hx-get='/plants/{plant}/table' hx-target='#content' hx-trigger='click' hx-swap='outerHTML'
                hx-indicator='#info'>
                    Carregar Tabela
                </button>
            </div>
            <div>
                <div>
                    <p>Nome: {plants_dict.get(plant).get('nome')}</p>
                    <p>Temperatura Mínima Registrada: {plants_dict.get(plant).get('temp').get('min')}ºC</p>
                    <p>Umidade Mínima Registrada: {plants_dict.get(plant).get('umid').get('min')}%</p>
                    <p>Valor do Sinal Mínimo Registrado: {plants_dict.get(plant).get('signal').get('min')}</p>
                </div>
                <div>
                    <p>Especie: {plants_dict.get(plant).get('especie')}</p>
                    <p>Temperatura Máxima Registrada: {plants_dict.get(plant).get('temp').get('max')}ºC</p>
                    <p>Umidade Máxima Registrada: {plants_dict.get(plant).get('umid').get('max')}%</p>
                    <p>Valor do Sinal Máximo Registrado: {plants_dict.get(plant).get('signal').get('max')}</p>
                </div>
            </div>
            <div id='content' class='htmx-indicator'><b>Carregando...</b></div>
        </section>
    '''

# @app.get('/plants/{plant}/graph', response_class=HTMLResponse)
# async def get_graph(plant):
#     df = get_plant_data(plant, limit=5000)
#     df['Temperatura'] = df['Temperatura'].apply(lambda x: float(x[:4]) * 0.01)
#     df['Umidade'] = df['Umidade'].apply(lambda x: int(x[:2]) * 0.01)
#     # return
    

@app.get('/plants/{plant}/table', response_class=HTMLResponse)
async def get_graph(plant):
    df = get_plant_data(plant, limit=5000)
    df['Temperatura'] = df['Temperatura'].apply(lambda x: float(x[:4]) * 0.01)
    df['Umidade'] = df['Umidade'].apply(lambda x: int(x[:2]) * 0.01)
    return f'''
        <div id='content'>
            <table>
                <tbody>
                    <tr><th>Valor do sinal</th><th>Temperatura</th><th>Umidade</th><th>Data</th><th>Hora</th></tr>
                    {
                        ''.join([
                            f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>'
                            for row in zip(df['Valor do sinal'], df['Temperatura'], df['Umidade'], df['Data'], df['Hora'])
                        ])
                    }
                </tbody>
            </table>
        </div>
    '''

@app.get('/plants/{plant}/data')
async def get_data(plant):
    return await get_plant_data(plant).to_json(orient='records')