from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from db.plant import AnnotatedSession, create_database_metadata, fetch_sensor_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database_metadata()
    yield

app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory='static'), name='static')

app.add_middleware(GZipMiddleware)

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return Jinja2Templates(directory='templates').TemplateResponse(request=request, name='index.html')

@app.get("/plants/sensor_data/")
async def get_sensor_data(session: AnnotatedSession):
    def generate():
        for chunk in fetch_sensor_data(session):
            yield chunk.to_json(
                orient='records', lines=True, date_format='iso', date_unit='s', 
                compression={'method': 'gzip', 'compresslevel': 1, 'mtime': 1}
            )
    return StreamingResponse(generate(), media_type='application/json')
    
@app.get("/plants/{plant_name}/sensor_data/") 
async def get_plant_data(plant_name: str, session: AnnotatedSession):
    def generate():
        for chunk in fetch_sensor_data(session, plant_name=plant_name):
            yield chunk.to_json(
                orient='records', lines=True, date_format='iso', date_unit='s', 
                compression={'method': 'gzip', 'compresslevel': 1, 'mtime': 1}
            )
    return StreamingResponse(generate(), media_type='application/json')

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

@app.get('/plants/{plant_name}/info', response_class=HTMLResponse)
async def get_info(plant_name):
    return f'''
        <section id='info'>
            <h3>Informações da planta</h3>
            <div>
                <button href='/plants/{plant_name}/graph' hx-get='/plants/{plant_name}/graph' hx-target='#content' hx-trigger='click' hx-swap='outerHTML' hx-indicator='#info'>
                    Carregar Gráfico
                </button>
                <button href='/plants/{plant_name}/table' hx-get='/plants/{plant_name}/table' hx-target='#content' hx-trigger='click' hx-swap='outerHTML'
                hx-indicator='#info'>
                    Carregar Tabela
                </button>
            </div>
            <div>
                <div>
                    <p>Nome: {plants_dict.get(plant_name).get('nome')}</p>
                    <p>Temperatura Mínima Registrada: {plants_dict.get(plant_name).get('temp').get('min')}ºC</p>
                    <p>Umidade Mínima Registrada: {plants_dict.get(plant_name).get('umid').get('min')}%</p>
                    <p>Valor do Sinal Mínimo Registrado: {plants_dict.get(plant_name).get('signal').get('min')}</p>
                </div>
                <div>
                    <p>Especie: {plants_dict.get(plant_name).get('especie')}</p>
                    <p>Temperatura Máxima Registrada: {plants_dict.get(plant_name).get('temp').get('max')}ºC</p>
                    <p>Umidade Máxima Registrada: {plants_dict.get(plant_name).get('umid').get('max')}%</p>
                    <p>Valor do Sinal Máximo Registrado: {plants_dict.get(plant_name).get('signal').get('max')}</p>
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
    
# @app.get('/plants/{plant}/table', response_class=HTMLResponse)
# async def get_graph(plant):
#     df = get_plant_data(plant, limit=5000)
#     df['Temperatura'] = df['Temperatura'].apply(lambda x: float(x[:4]) * 0.01)
#     df['Umidade'] = df['Umidade'].apply(lambda x: int(x[:2]) * 0.01)
#     return f'''
#         <div id='content'>
#             <table>
#                 <tbody>
#                     <tr><th>Valor do sinal</th><th>Temperatura</th><th>Umidade</th><th>Data</th><th>Hora</th></tr>
#                     {
#                         ''.join([
#                             f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>'
#                             for row in zip(df['Valor do sinal'], df['Temperatura'], df['Umidade'], df['Data'], df['Hora'])
#                         ])
#                     }
#                 </tbody>
#             </table>
#         </div>
#     '''