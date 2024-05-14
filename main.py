from os import listdir
from datetime import datetime
from os.path import join, dirname, abspath

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

plants = {
    'excaulebur': {
        'genero': {},
        'especie': {}
    },
    'totosa': {
        'genero': {},
        'especie': {}
    }
}

def get_plant_data(plant):
    with open(join(dirname(abspath(__file__)), 'data', f'{plant.title()}.csv'), 'r') as f: 
        return pd.read_csv(f, encoding='unicode_escape', engine='python')

def concat_plant_data(plant):
    df = pd.concat([get_file_data(file, plant) for file in listdir(join(dirname(abspath(__file__)), 'data'))])
    return df.sort_values(by=['Data', 'Hora']).to_csv(f'./data/{plant.title()}.csv', index=False)

def get_file_data(file, plant):
    if file.split('_')[0] == plant.title():
        with open(join(dirname(abspath(__file__)), 'data', file), 'r') as f:
            df = pd.read_csv(f, encoding='unicode_escape', engine='python')
            df['Data'] = file.split('.')[0][-10:]
            return df[['Valor do sinal', 'Temperatura', 'Umidade', 'Data', 'Hora']]

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory='templates')

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.get('/plants/{plant}/info', response_class=HTMLResponse)
def get_plant_info(plant):
    return f'''
        <section id="info">
            <p>info about {plant}</p>
            <button hx-get="plants/{plant}/table">check the data</button>
        </section>
    '''


@app.get('/plants/{plant}/table', response_class=HTMLResponse)
def get_plant_table(plant):
    df = get_plant_data(plant)
    return f'''
        <table>
            <tbody>
                <tr>
                    <td>Valor do sinal</td>
                    <td>Temperatura</td>
                    <td>Umidade</td>
                    <td>Data</td>
                    <td>Hora</td>
                </tr>
                {
                    ''.join([
                        f"""
                            <tr>
                                <td>{row[0]}</td>
                                <td>{row[1].replace('Â', '')}</td>
                                <td>{row[2]}</td>
                                <td>{datetime.strptime(row[3], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                                <td>{row[4]}</td>
                            </tr>
                        """
                        for row in zip(df['Valor do sinal'], df['Temperatura'], df['Umidade'], df['Data'], df['Hora'])
                    ])
                }
            </tbody>
        </table>
    '''

@app.get('/plants/{plant}/data')
def get_plant_data(plant):
    return get_plant_data(plant).to_json(orient='records')