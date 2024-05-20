from os import listdir
from datetime import datetime
from os.path import join, dirname, abspath

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

plants_dict = {
    'excaulebur': {
        'nome': 'Excalibur',
        'especie': 'Dracaena Trifasciata'
    },
    'totosa': {
        'nome': 'Totosa',
        'especie': 'Portulacaria Afra'
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
            df['Data'] = file.split('.')[0][-10:]
            return df[['Valor do sinal', 'Temperatura', 'Umidade', 'Data', 'Hora']]
        
def concat_plant_data(plant):
    df = pd.concat([get_file_data(file, plant) for file in listdir(join(dirname(abspath(__file__)), 'data'))])
    return df.sort_values(by=['Data', 'Hora']).to_csv(f'./data/{plant.title()}.csv', index=False)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory='templates')

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@app.get('/plants/{plant}/info', response_class=HTMLResponse)
def get_info(plant):
    df = get_plant_data(plant)
    df['Temperatura'] = df['Temperatura'].apply(lambda x: float(x[:4]))
    df['Umidade'] = df['Umidade'].apply(lambda x: int(x[:2]))
    return f'''
        <section id="info">
            <h3>Informações da planta</h3>
            <div>
                <div>
                    <p>Nome: {plants_dict.get(plant).get('nome')}</p>
                    <p>Temperatura Mínima Registrada: {df['Temperatura'].min()}ºC</p>
                    <p>Umidade Mínima Registrada: {df['Umidade'].min()}%</p>
                    <p>Valor do Sinal Mínimo Registrado: {df['Valor do sinal'].min()}</p>
                </div>
                <div>
                    <p>Especie: {plants_dict.get(plant).get('especie')}</p>
                    <p>Temperatura Máxima Registrada: {df['Temperatura'].max()}ºC</p>
                    <p>Umidade Máxima Registrada: {df['Umidade'].max()}%</p>
                    <p>Valor do Sinal Máximo Registrado: {df['Valor do sinal'].max()}</p>
                </div>
            </div>
            <div>
                <table>
                    <tbody>
                        <tr>
                            <th>Valor do sinal</th>
                            <th>Temperatura</th>
                            <th>Umidade</th>
                            <th>Data</th>
                            <th>Hora</th>
                        </tr>
                        {
                            ''.join([
                                f"""
                                    <tr>
                                        <td>{row[0]}</td>
                                        <td>{row[1]}</td>
                                        <td>{row[2]}</td>
                                        <td>{row[3]}</td>
                                        <td>{row[4]}</td>
                                    </tr>
                                """
                                for row in zip(df['Valor do sinal'], df['Temperatura'], df['Umidade'], df['Data'], df['Hora'])
                            ])
                        }
                    </tbody>
                </table>
            </div>
        </section>
    '''

@app.get('/plants/{plant}/data')
def get_data(plant):
    return get_plant_data(plant).to_json(orient='records')