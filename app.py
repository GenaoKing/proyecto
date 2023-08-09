from flask import Flask, request, jsonify, Response, render_template,url_for,redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import pyodbc
from flask_cors import CORS
import cv2
import os
import time
import numpy as np
from contextlib import contextmanager
import datetime
from werkzeug.exceptions import abort
import yaml
from ultralytics import YOLO
import pandas as pd
from dateutil.relativedelta import relativedelta



os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
app = Flask(__name__)
app.secret_key = 'proyecto'
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)


image_processing_completed = False  # Añadir esto al principio
sensor_data_inserted = False  # Añadir esto al principio
sensor_data = []
flag_ready = False
capture_flag = False
max_hoja_id = None
category_id = None
userid = None
rutaCarpetaImagenes = None
rutaCarpetaEtiquetas = None
user = None
modelid = None
modelname = None

class User(UserMixin):
    def __init__(self, username, password,is_admin,idusuario):
        self.id = username
        self.password = password
        self.is_admin = is_admin
        self.idusuario = idusuario


@app.route('/get_admin', methods=['GET'])
@login_required
def get_admin():
    return jsonify(current_user.is_admin)

@contextmanager
def db_connection():
    server = 'DESKTOP-MSLG0IL'  # Reemplaza con el nombre de tu servidor
    database = 'Tabaco'  # Reemplaza con el nombre de tu base de datos

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=' + server +
                          ';DATABASE=' + database + ';Trusted_Connection=yes;''TrustServerCertificate=yes;')
    cursor = cnxn.cursor()
    try:
        yield cursor
    finally:
        cnxn.commit()
        cursor.close()
        cnxn.close()


@app.route('/get_username', methods=['GET'])
@login_required
def get_username():
    return jsonify(username=current_user.id), 200

@login_manager.user_loader
def load_user(username):
    
    with db_connection() as cursor:
        
        cursor.execute('SELECT username, password,admin,IdUsuario FROM [User] WHERE username = ?', (username,))
        result = cursor.fetchone()
        if result:
            
            return User(*result)
        
        else:
            return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    global userid
    global user
    if request.method == 'POST':
        with db_connection() as cursor:
            cursor.execute('SELECT password,admin,IdUsuario FROM [User] WHERE username = ?', (request.form['username'],))
            result = cursor.fetchone()
            if result and check_password_hash(result[0], request.form['password']):
                user = User(request.form['username'], result[0],result[1],result[2])
                cursor.execute('SELECT IdUsuario FROM [User] WHERE username = ?', (request.form['username'],))
                userid = cursor.fetchone()[0]
                login_user(user)
               
                return redirect(url_for('index'))
            else:
                return 'Invalid username or password'
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




@app.route('/')
@login_required
def index():
    with db_connection() as cursor:
        global max_hoja_id
        cursor.execute('SELECT MAX(HojaId) FROM Hoja')
        max_hoja_id = cursor.fetchone()[0]

        # Si la tabla está vacía, asignar 1 como el primer HojaId, de lo contrario, incrementar el máximo HojaId en 1
        if max_hoja_id is None:
                max_hoja_id = 1
        else:
                max_hoja_id = max_hoja_id + 1
                
        return render_template('index.html')
    

@app.route('/entrenamiento')
@login_required
def entrenamiento():
    if current_user.is_admin:
        return render_template('entrenamiento.html')
    else:
        return render_template('index.html')
    
@app.route('/reporteria')
@login_required
def reporteria():
    if current_user.is_admin:
        return render_template('reporteria.html')
    else:
        return render_template('index.html')

@app.route('/captura')
@login_required
def captura():
    return render_template('captura.html')

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
        if current_user.is_admin:
            if request.method == 'POST':
                # Asegúrate de que solo los administradores puedan acceder a este endpoint
                if not current_user.is_admin:
                    return jsonify({"error": "Solo los administradores pueden crear usuarios"}), 403

                data = request.get_json()

                username = data.get('username')
                password = data.get('password')
                security_question = data.get('securityQuestion')
                security_answer = data.get('securityAnswer')
                is_admin = data.get('isAdmin')
                # Validación básica de los datos
                if not all([username, password, security_question, security_answer, is_admin is not None]):
                    return jsonify({"error": "Faltan datos"}), 400

                # Encripta la contraseña antes de guardarla en la base de datos
                hashed_password = generate_password_hash(password)
                hashed_answer = generate_password_hash(security_answer)
                with db_connection() as cursor:
                    # Comprueba si el nombre de usuario ya existe
                    cursor.execute('SELECT username FROM [User] WHERE username = ?', (username,))
                    result = cursor.fetchone()
                    if result:
                        return jsonify({"error": "El nombre de usuario ya existe"}), 400

                    # Inserta el nuevo usuario en la base de datos
                    cursor.execute(
                        'INSERT INTO [User] (username, password, pregunta, respuesta, admin, registrado) VALUES (?, ?, ?, ?, ?,GETDATE())',
                        (username, hashed_password, security_question, hashed_answer, is_admin)
                    )
                return jsonify({"success": "Usuario creado con éxito"}), 201 
            
            else:
                return render_template('configuracion.html')
        else:
            return render_template('index.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        security_question_id = int(request.form['securityQuestion'])
        answer = request.form['answer']

        with db_connection() as cursor:
            cursor.execute('SELECT pregunta, respuesta FROM [User] WHERE username = ?', (username,))
            result = cursor.fetchone()

            # Si el usuario no existe en la base de datos
            if result is None:
                return render_template('forgot_password.html', error='Nombre de usuario no encontrado')

            db_security_question_id, db_answer_hash = result

            # Comprueba si la pregunta de seguridad coincide
            if db_security_question_id != security_question_id:
                return render_template('forgot_password.html', error='La pregunta de seguridad no coincide')

            # Comprueba si la respuesta coincide
            if not check_password_hash(db_answer_hash, answer):
                return render_template('forgot_password.html', error='La respuesta no coincide')

            # Si todo es correcto, redirige a la página de restablecimiento de contraseña
            return redirect(url_for('reset_password', username=username))

    return render_template('forgot_password.html')

@app.route('/users', methods=['GET'])
@login_required
def get_users():
    if current_user.is_admin:
        with db_connection() as cursor:
            # Hacemos la consulta para traer la información de los usuarios junto con la cantidad de hojas analizadas
            cursor.execute('''
                        SELECT U.IdUsuario, U.Username, U.Registrado, 
                                COALESCE((SELECT COUNT(*) FROM Hoja H WHERE U.IdUsuario = H.IdUsuario), 0)
                        FROM [User] U
            ''')
            users = cursor.fetchall()

            data = []

            for user in users:
                data.append({
                    "id": user[0],
                    "username": user[1],
                    "registrationDate": user[2].isoformat(),
                    "analyzedSheets": user[3]
                })

        return jsonify(data)


@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        new_password = request.form['newPassword']
        confirm_password = request.form['confirmPassword']
        if new_password != confirm_password:
            return render_template('reset_password.html', error='Las contraseñas no coinciden')

        hashed_new_password = generate_password_hash(new_password)

        with db_connection() as cursor:
            cursor.execute(
                'UPDATE [User] SET password = ? WHERE username = ?',
                (hashed_new_password, username)
            )

            # Si se actualizó una fila, entonces la operación fue exitosa
            if cursor.rowcount == 1:
                return redirect(url_for('login'))
            else:
                return render_template('reset_password.html', error='Nombre de usuario no encontrado')

    return render_template('reset_password.html')

@app.route('/categorias', methods=['GET'])
@login_required
def get_categorias():
    with db_connection() as cursor:
        # Consultar cada categoria
        cursor.execute('SELECT * FROM Categoria')
        rows = cursor.fetchall()

        # Obtener los nombres de las columnas desde el cursor
        column_names = [column[0] for column in cursor.description]

        # Convertir cada fila en un diccionario
        categorias = [dict(zip(column_names, row)) for row in rows]

    return jsonify(categorias), 200



@app.route('/average_band_values', methods=['GET'])
@login_required
def get_average_band_values():
    # Iniciar una lista vacía para almacenar los datos
    data = []

    with db_connection() as cursor:
        # Consultar cada categoria
        cursor.execute('SELECT * FROM Categoria')
        categories = cursor.fetchall()

        for category in categories:
            # Para cada categoria, consultar los valores de banda promedio
            cursor.execute('''
                SELECT Banda.Longitud, AVG(Mediciones.Valor)
                FROM Mediciones
                JOIN Hoja ON Mediciones.HojaId = Hoja.HojaId
                JOIN Banda ON Mediciones.BandaId = Banda.BandaId
                WHERE Hoja.IdCategoria = ?
                GROUP BY Banda.Nombre, Banda.Longitud
                ORDER BY Banda.Longitud
            ''', (category.IdCategoria,))
            
            # Transformar los datos en un diccionario y añadirlo a la lista
            band_values = [{'wavelength': name, 'value': value} for name, value in cursor.fetchall()]
            data.append({
                'category': category.Descripcion,
                'values': band_values
            })

    # Devolver los datos como un objeto JSON
    return jsonify(data), 200


@app.route('/informes_modelo', methods=['GET'])
@login_required
def informes_modelo():
    # Obtener los filtros de la solicitud
    if current_user.is_admin:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        with db_connection() as cursor:
            # Realiza una consulta para obtener el nombre del modelo, la fecha de creación, el nombre de usuario y las hojas analizadas
            query = '''SELECT m.Descripcion, m.Fecha, u.Username, COUNT(h.HojaId)
                    FROM Modelo m JOIN [User] u ON m.IdUsuario = u.IdUsuario
                    JOIN Hoja h ON h.IdModelo = m.IdModelo
                    WHERE h.Fecha >= ? AND h.Fecha <= ?
                    GROUP BY m.Descripcion, m.Fecha, u.Username'''
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

        # Inicializa la lista para almacenar los datos del informe
        informes_modelo = []

        # Recorre los resultados de la consulta SQL
        for result in results:
            nombre = result[0]
            fecha = result[1]
            usuario = result[2]
            hojas = result[3]

            model_dir = os.path.join('modelos', nombre)
            entrenamientos = len([folder for folder in os.listdir(model_dir) if folder.startswith("train") and os.path.isdir(os.path.join(model_dir, folder))])
        
            if entrenamientos == 0:
                return jsonify({"error": "Este modelo no se ha entrenado"}), 400
            elif entrenamientos == 1:
                last_train_dir = os.path.join(model_dir, 'train')
            else :
                last_train_dir = os.path.join(model_dir, f'train{entrenamientos}')
            
            
            result_file = os.path.join(last_train_dir, 'results.csv')

            # Lee el archivo CSV de resultados y encuentra la máxima precisión
            df = pd.read_csv(result_file)
            precision = df['   metrics/precision(B)'].max()

            # Añade los datos del modelo al informe
            informes_modelo.append({
                'nombre': nombre,
                'fecha': fecha.strftime('%d de %B del %Y'),  # Formatea la fecha a una cadena
                'entrenamientos': entrenamientos,
                'usuario': usuario,
                'hojas': hojas,
                'precision': precision,
            })

        return jsonify(informes_modelo), 200


@app.route('/informes_categoria', methods=['GET'])
@login_required
def informes_categoria():
    # Obtener los filtros de la solicitud
    if current_user.is_admin:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')

        with db_connection() as cursor:
            # Realiza una consulta para obtener las características de las hojas y su categoría correspondiente
            query = 'SELECT h.Longitud, h.Ancho, h.Area, c.Descripcion FROM Hoja h JOIN Categoria c ON h.IdCategoria = c.IdCategoria WHERE h.Fecha >= ? AND h.Fecha <= ? AND c.IdCategoria = ?'
            cursor.execute(query, (start_date, end_date, category))
            results = cursor.fetchall()

            # Continuación del código existente...

            # Transforma los resultados en un objeto JSON
            hojas_data = []
            for result in results:
                hojas_data.append({
                    'longitud': result[0],
                    'ancho': result[1],
                    'area': result[2],
                    'categoria': result[3]
                })

            # Creamos un dataframe de pandas con nuestros datos
            df = pd.DataFrame(hojas_data)

            # Agrupamos los datos por categoría y calculamos los cuartiles, la suma del área, y el número de hojas para cada característica
            grouped = df.groupby('categoria').agg({
                'longitud': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max')],
                'ancho': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max')],
                'area': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max'), ('sum', 'sum'), ('count', 'count')],
            })

            # Añadimos el cálculo del promedio y la distribución del área
            grouped['area', 'mean'] = df.groupby('categoria')['area'].mean()
            


            # Procesamos los resultados en el formato que espera el cliente
            informes_categoria = []
            for categoria, data_categoria in grouped.iterrows():
                informes_categoria.append({
                    'categoria': categoria,
                    'longitud': {'min': data_categoria[('longitud', 'min')], 'q1': data_categoria[('longitud', 'q1')], 'median': data_categoria[('longitud', 'median')], 'q3': data_categoria[('longitud', 'q3')], 'max': data_categoria[('longitud', 'max')]},
                    'ancho': {'min': data_categoria[('ancho', 'min')], 'q1': data_categoria[('ancho', 'q1')], 'median': data_categoria[('ancho', 'median')], 'q3': data_categoria[('ancho', 'q3')], 'max': data_categoria[('ancho', 'max')]},
                    'area': {'min': data_categoria[('area', 'min')], 'q1': data_categoria[('area', 'q1')], 'median': data_categoria[('area', 'median')], 'q3': data_categoria[('area', 'q3')], 'max': data_categoria[('area', 'max')], 'sum': data_categoria[('area', 'sum')], 'count': data_categoria[('area', 'count')], 'mean': data_categoria[('area', 'mean')]},
                })

            return jsonify(informes_categoria), 200


@app.route('/hojas_data', methods=['GET'])
@login_required
def hojas_data():
    categoria_id = request.args.get('categoria_id', default = 0, type = int)

    with db_connection() as cursor:
        # Realiza una consulta para obtener las características de las hojas y su categoría correspondiente
        if categoria_id > 0:
            cursor.execute('SELECT h.Longitud, h.Ancho, h.Area, c.Descripcion FROM Hoja h JOIN Categoria c ON h.IdCategoria = c.IdCategoria WHERE c.IdCategoria = ?', [categoria_id])
        else:
            cursor.execute('SELECT h.Longitud, h.Ancho, h.Area, c.Descripcion FROM Hoja h JOIN Categoria c ON h.IdCategoria = c.IdCategoria')
        
        results = cursor.fetchall()

        # Transforma los resultados en un objeto JSON
        hojas_data = []
        for result in results:
            hojas_data.append({
                'longitud': result[0],
                'ancho': result[1],
                'area': result[2],
                'categoria': result[3]
            })

        # Creamos un dataframe de pandas con nuestros datos
        df = pd.DataFrame(hojas_data)

        # Agrupamos los datos por categoría y calculamos los cuartiles para cada característica
        grouped = df.groupby('categoria').agg({
            'longitud': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max')],
            'ancho': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max')],
            'area': [('min', 'min'), ('q1', lambda x: x.quantile(0.25)), ('median', 'median'), ('q3', lambda x: x.quantile(0.75)), ('max', 'max')]
        })

        # Reorganizamos los datos en el formato que espera el gráfico boxplot
        hojas_boxplot_data = []
        for categoria, data_categoria in grouped.iterrows():
            hojas_boxplot_data.append({
                'categoria': categoria,
                'longitud': {
                    'min': round(data_categoria[('longitud', 'min')], 2), 
                    'q1': round(data_categoria[('longitud', 'q1')], 2), 
                    'median': round(data_categoria[('longitud', 'median')], 2), 
                    'q3': round(data_categoria[('longitud', 'q3')], 2), 
                    'max': round(data_categoria[('longitud', 'max')], 2)
                },
                'ancho': {
                    'min': round(data_categoria[('ancho', 'min')], 2), 
                    'q1': round(data_categoria[('ancho', 'q1')], 2), 
                    'median': round(data_categoria[('ancho', 'median')], 2), 
                    'q3': round(data_categoria[('ancho', 'q3')], 2), 
                    'max': round(data_categoria[('ancho', 'max')], 2)
                },
                'area': {
                    'min': round(data_categoria[('area', 'min')], 2), 
                    'q1': round(data_categoria[('area', 'q1')], 2), 
                    'median': round(data_categoria[('area', 'median')], 2), 
                    'q3': round(data_categoria[('area', 'q3')], 2), 
                    'max': round(data_categoria[('area', 'max')], 2)
                }
            })

        return jsonify(hojas_boxplot_data), 200


@app.route('/hojas_por_intervalo', methods=['GET'])
@login_required
def get_hojas_por_intervalo():
    with db_connection() as cursor:
        intervalo = request.args.get('intervalo')
        if intervalo not in ['dia', 'semana', 'mes']:
            return jsonify({"error": "Intervalo no válido"}), 400

        ahora = datetime.datetime.now()
        if intervalo == 'dia':
            desde = ahora - datetime.timedelta(days=7)
            cursor.execute("""
                SELECT COUNT(HojaId) as Cantidad, CAST(Fecha as DATE) as Fecha
                FROM Hoja
                WHERE Fecha >= ?
                GROUP BY CAST(Fecha as DATE)
                ORDER BY Fecha DESC
            """, (desde,))
        if intervalo == 'semana':
            desde = ahora - datetime.timedelta(weeks=7)
            cursor.execute("""
                SELECT COUNT(HojaId) as Cantidad, 
                DATEADD(wk, DATEDIFF(wk, 0, Fecha), 0) as Fecha
                FROM Hoja
                WHERE Fecha >= ?
                GROUP BY DATEADD(wk, DATEDIFF(wk, 0, Fecha), 0)
                ORDER BY Fecha DESC
            """, (desde,))
        elif intervalo == 'mes':
            desde = ahora - relativedelta(months=7)
            cursor.execute("""
                SELECT COUNT(HojaId) as Cantidad, 
                DATEADD(mm, DATEDIFF(mm, 0, Fecha), 0) as Fecha
                FROM Hoja
                WHERE Fecha >= ?
                GROUP BY DATEADD(mm, DATEDIFF(mm, 0, Fecha), 0)
                ORDER BY Fecha DESC
            """, (desde,))
        
        hojas = cursor.fetchall()
        hojas_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in hojas]
        
        # Convertir las fechas a formato ISO 8601
        for hoja in hojas_dict:
            if 'Fecha' in hoja:
                hoja['Fecha'] = hoja['Fecha'].isoformat()
        
        return jsonify(hojas_dict)



@app.route('/video_feed', methods=['GET'])
@login_required
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/hojas', methods=['GET'])
@login_required
def get_hojas():
    with db_connection() as cursor:
        cursor.execute('''SELECT h.HojaId, h.Longitud,h.Ancho, h.Fecha,h.Area,c.Descripcion,m.descripcion as modelo,u.username
                       FROM Hoja h, Categoria C, Modelo M, [User] u 
                       Where H.IdCategoria = C.IdCategoria and H.IdModelo = M.IdModelo and H.IdUsuario = u.IdUsuario
                       Order By h.Fecha desc''')
        hojas = cursor.fetchall()
        hojas_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in hojas]
        return jsonify(hojas_dict)


@app.route('/get_latest_hoja_id', methods=['GET'])
@login_required
def get_latest_hoja_id():
    with db_connection() as cursor:
        cursor.execute('SELECT MAX(hojaId) FROM hoja')
        result = cursor.fetchone()
        if result:
            
            max_hoja_id = result[0]
            return jsonify(max_hoja_id), 200
        else:
            return jsonify(message="No records found"), 404



@app.route('/set_flag', methods=['POST'])
@login_required
def set_flag():
    global capture_flag
    global category_id
    global flag_ready
    global image_processing_completed  # Añadir esto
    global sensor_data_inserted  # Añadir esto
    flag_ready = False
    image_processing_completed = False  # Añadir esto
    sensor_data_inserted = False  # Añadir esto
    capture_flag = True
    data = request.get_json()  # obteniendo el cuerpo de la solicitud
    category_id = data.get('categoriaId')  # extrayendo el category_id
    requests.post('http://192.168.43.187/set_flag', data='true')
    return '',200

@app.route('/data', methods=['POST'])
def handle_data():
    global sensor_data
    global capture_flag
    global modelname
    # Obtener los datos JSON enviados en la solicitud
    data = request.get_json()

    # Hacer algo con los datos recibidos
    device_id = data['device_id']
    as7265x_data = data['data']
    #insert_data(as7265x_data)
    sensor_data = as7265x_data
    
    # Responder con un mensaje de éxito
    #capture_flag = True
    insert_data(sensor_data)
    return 'Datos recibidos correctamente.'

@app.route('/sensor_data', methods=['GET'])
@login_required
def get_sensor_data():
    global sensor_data
    return jsonify(sensor_data)

@app.route('/get_hoja_data/<string:hoja_id>')
@login_required
def get_hoja_data(hoja_id):
    with db_connection() as cursor:
        cursor.execute('SELECT Valor FROM Mediciones WHERE HojaId='+hoja_id)
        hojas = list(cursor.fetchall())
        hojas_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in hojas]
        return jsonify(hojas_dict)


@app.route('/get_totales', methods=['GET'])
@login_required
def get_totales():
    with db_connection() as cursor:
        cursor.execute('SELECT C.Descripcion, COUNT(*) AS Total FROM HOJA AS H, Categoria AS C WHERE C.IdCategoria = H.IdCategoria GROUP BY C.IdCategoria, C.Descripcion')
        total = list(cursor.fetchall())
        total_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in total]
        return jsonify(total_dict)
    

@app.route('/guardar_modelo', methods=['POST'])
@login_required
def guardar_modelo():
    if current_user.is_admin:
        global userid
        global rutaCarpetaImagenes, rutaCarpetaEtiquetas
        data = request.get_json()
        nombreModelo = data.get('nombreModelo')
        if not nombreModelo:
            return jsonify({ 'error': 'No se proporcionó el nombre del modelo' }), 400

        # Crea una nueva ruta para el modelo
        rutaModelo = os.path.join('modelos', nombreModelo)

        # Comprueba si ya existe una carpeta con el mismo nombre
        if os.path.exists(rutaModelo):
            with db_connection() as cursor:
                try:
                    cursor.execute('UPDATE Modelo SET IdUsuario = ?, Fecha = GETDATE() WHERE Descripcion = ?', (userid, nombreModelo))

                    rutaCarpetaImagenes = os.path.join(rutaModelo, 'images')
                    rutaCarpetaEtiquetas = os.path.join(rutaModelo, 'labels')
                except Exception as e:
                    return jsonify({ 'error': 'Error al insertar en la base de datos: ' + str(e) }), 500
            return jsonify({ 'message': 'Ya existia este modelo, esta actualizado el dataset' }), 200

        # Crea la nueva carpeta para el modelo
        os.makedirs(rutaModelo)

        rutaCarpetaImagenes = os.path.join(rutaModelo, 'images')
        rutaCarpetaEtiquetas = os.path.join(rutaModelo, 'labels')
        os.makedirs(rutaCarpetaImagenes)
        os.makedirs(rutaCarpetaEtiquetas)

        # Crea el nuevo registro en la tabla Modelo
        with db_connection() as cursor:
            try:
                cursor.execute(
                    'INSERT INTO Modelo (Descripcion, Fecha, IdUsuario, Ruta) VALUES (?, GETDATE(), ?, ?)',
                    (nombreModelo, userid, rutaModelo)
                )
                
            except Exception as e:
                error_message = e.args[1] if len(e.args) > 1 else e.args[0]
                return jsonify({ 'error': 'Error al insertar en la base de datos: ' + str(e) }), 500

        return jsonify({ 'message': 'Modelo guardado correctamente' })

def generate_frames():

    with db_connection() as cursor:
        

        camera = cv2.VideoCapture(1)
        global capture_flag
        global max_hoja_id
        # Establecer la resolución de la cámara a HD (1920x1080)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        camera.set(cv2.CAP_PROP_FPS, 30)
        

        while True:
            success, frame = camera.read()

            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                if capture_flag:
                    store_image(buffer) 
        
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        camera.release()



def store_image(buffer):
    global capture_flag
    global category_id
    global modelid
    global modelname
    if modelid is None:
        file_path = os.path.join(
        'captured_images', f'image_{max_hoja_id}.jpg')
        cv2.imwrite(file_path, cv2.imdecode(buffer, -1))
        capture_flag = False
        image_process(file_path)

    elif modelid is not None:
        file_path = os.path.join(
        'captured_images', f'image_{max_hoja_id}.jpg')
        cv2.imwrite(file_path, cv2.imdecode(buffer, -1))
        
        capture_flag = False
        capture_predict(file_path)
    
    capture_flag = False
    modelid = None
    modelname = None

def capture_predict(file_path):
    global modelid
    global modelname
    global category_id
    global modelo
    global flag_ready
    global image_processing_completed
    directory_path = "modelos/" + modelname
    all_folders = os.listdir(directory_path)
    train_folders = [folder for folder in all_folders if folder.startswith("train")]
    train_folders.sort()
    latest_train_folder = train_folders[-1]
    model_path = os.path.join(directory_path, latest_train_folder, "weights", "best.pt")
    model = YOLO(model_path)


    image = cv2.imread(file_path)
    img = image
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_blue = cv2.inRange(hsv, (70, 90, 0), (150, 255, 255))
    nmask = cv2.bitwise_not(mask_blue)

    res = cv2.bitwise_and(img,img, mask= nmask )
    res = cv2.medianBlur(res,7)

    gray = cv2.cvtColor((cv2.cvtColor(res, cv2.COLOR_HSV2BGR)),cv2.COLOR_BGR2GRAY)

    contours, hierarchy = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour

    if max_contour is not None:
        mask = np.zeros_like(img)
        cv2.drawContours(mask, [max_contour], -1, (255,255,255), thickness=cv2.FILLED)
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        x, y, w, h = cv2.boundingRect(max_contour)
        width= round(h * 0.0344,2)
        height= round(w * 0.0314,2)

    foreground = cv2.bitwise_and(img, img, mask=mask_gray)
    #file_path = os.path.join('static', f'image_{max_hoja_id}.jpg')
    #cv2.imwrite(file_path,foreground)

   

    results = model.predict(foreground, verbose=False)
    requests.post('http://192.168.43.187/set_flag', data='true')
    #res = results[0].plot()
    file_path = os.path.join('static', f'image_{max_hoja_id}.jpg')
    output = results[0].boxes[0].data
    #cv2.imwrite(file_path,res)
    x1, y1, x2, y2 = map(int, output[0][:4].tolist())
    score = float(output[0][4])
    label = int(output[0][5])
    category_id = label + 1
    name = results[0].names[label]
    # Cargamos la imagen
    # img = cv2.imread("ruta_de_tu_imagen")

    # Dibujamos el bounding box en la imagen
    cv2.rectangle(foreground, (x1, y1), (x2, y2), (0, 255, 0), 2) # Bounding box con línea verde y grosor 2

    # Si deseas añadir el score y el label en la esquina superior izquierda del bounding box
    cv2.putText(foreground, f'{name}:{score:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    cv2.imwrite(file_path,foreground)
    
    a=round((max_area * 0.0344 * 0.0314),2)
    insert_lw(max_hoja_id,(width,height),a,modelid)
    flag_ready = True
    image_processing_completed = True
    

def insert_data(data):
    with db_connection() as cursor:
        global max_hoja_id
        global sensor_data_inserted  # Añadir esto
        insert_query = '''
        INSERT INTO Mediciones (HojaId, BandaId, Valor)
        VALUES (?, ?, ?)
        '''
        # Insertar cada banda en una fila separada con el siguiente HojaId
        for banda_id, valor in enumerate(data, start=1):
            cursor.execute(insert_query, (max_hoja_id, banda_id, valor))
        
        max_hoja_id = max_hoja_id+1
     
    
        sensor_data_inserted = True
        
         
def insert_lw(next_hoja_id, res, a, id_modelo):
    with db_connection() as cursor:    
        global max_hoja_id
        global category_id
        global userid
        insert_query = '''
        INSERT INTO Hoja (HojaId, Ancho, Longitud, IdCategoria, Area, Fecha, IdModelo,IdUsuario)
        VALUES (?, ?, ?, ?, ?, GETDATE(), ?,?)
        '''

        
        cursor.execute(insert_query, (next_hoja_id, res[0], res[1], category_id, a, id_modelo,userid))

       


def image_process(image_path):
    global sensor_data
    global category_id
    global rutaCarpetaEtiquetas
    global rutaCarpetaImagenes
    global flag_ready
    global image_processing_completed
    label_folder = 'data/labels'

    image = cv2.imread(image_path)
    img = image
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_blue = cv2.inRange(hsv, (70, 90, 0), (150, 255, 255))
    nmask = cv2.bitwise_not(mask_blue)

    res = cv2.bitwise_and(img,img, mask= nmask )
    res = cv2.medianBlur(res,7)

    gray = cv2.cvtColor((cv2.cvtColor(res, cv2.COLOR_HSV2BGR)),cv2.COLOR_BGR2GRAY)

    contours, hierarchy = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour

    if max_contour is not None:
        mask = np.zeros_like(img)
        cv2.drawContours(mask, [max_contour], -1, (255,255,255), thickness=cv2.FILLED)
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        x, y, w, h = cv2.boundingRect(max_contour)
        x_center = (x + w / 2) / img.shape[1]
        y_center = (y + h / 2) / img.shape[0]
        wid = w / img.shape[1]
        hei = h / img.shape[0]
        categoria = int(category_id)-1

        # Escribe el label en formato YOLO en un archivo .txt.
        label_filename = os.path.splitext(os.path.basename(image_path))[0] + '.txt'
        label_path = os.path.join(label_folder, label_filename)
        with open(label_path, 'w') as f:
            f.write(f'{categoria} {x_center} {y_center} {wid} {hei}')

        label_path = os.path.join(rutaCarpetaEtiquetas, label_filename)
        with open(label_path, 'w') as f:
            f.write(f'{categoria} {x_center} {y_center} {wid} {hei}')

        width= round(h * 0.0344,2)
        height= round(w * 0.0314,2)

    foreground = cv2.bitwise_and(img, img, mask=mask_gray)
    
    a=round((max_area * 0.0344 * 0.0314),2)
    id_modelo = get_model_id(os.path.basename(os.path.dirname(rutaCarpetaImagenes)))
    insert_lw(max_hoja_id,(width,height),a,id_modelo)
    file_path = os.path.join('static', f'image_{max_hoja_id}.jpg')
    cv2.imwrite(file_path,foreground)
    file_path = os.path.join(rutaCarpetaImagenes, f'image_{max_hoja_id}.jpg')
    cv2.imwrite(file_path,foreground)
    flag_ready = True
    image_processing_completed = True
    

@app.route('/ready', methods=['GET'])
@login_required
def ready():
     global flag_ready
     global image_processing_completed  # Añadir esto
     global sensor_data_inserted  # Añadir esto
     if flag_ready and image_processing_completed and sensor_data_inserted:  # Añadir las nuevas condiciones aquí
         return jsonify({"success": flag_ready}), 200
     return jsonify({"failed": flag_ready}), 400

     

def get_model_id(model_name):
    with db_connection() as cursor:
        select_query = "SELECT IdModelo FROM Modelo WHERE Descripcion = ?"
        cursor.execute(select_query, (model_name,))
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None  # o puedes manejar este caso como prefieras


def generate_config(model_name, names):
    # La ruta al directorio del modelo.
    model_path = f"C:\\Users\\santi\\Proyecto\\modelos\\{model_name}"

    # Convertir la lista 'names' a un diccionario donde la clave es el índice y el valor es el nombre.
    names_dict = {i: name for i, name in enumerate(names)}

    # Configuración para guardar en el archivo yaml.
    data = {
        'path': model_path,
        'train': 'images',
        'val': 'images',
        'names': names_dict  # Agrega 'names_dict' directamente a 'data'.
    }

    # Guardar la configuración en un archivo yaml.
    with open(f"{model_path}\\config.yaml", 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)



@app.route('/train_model/<model_name>', methods=['POST'])
@login_required
def train(model_name):
    # Generar el archivo de configuración.
    generate_config(model_name, ['Grande', 'Mediano', 'Pequeno', 'Roto', 'Tripa'])

    # Ruta al archivo de configuración.
    config_path = f"C:\\Users\\santi\\Proyecto\\modelos\\{model_name}"  # Asegúrate de incluir 'modelos' en la ruta.

    # Entrenar el modelo.
    train_model(config_path)

    # Devolver una respuesta.
    return 'Training has completed', 200




def train_model(config_path):
    model = YOLO("yolov8m.yaml")
    config_file = os.path.join(config_path, 'config.yaml')  # Ruta al archivo de configuración.
    results = model.train(data=config_file, epochs=100, project=config_path)  # Usar 'config_file' para 'data' y 'config_path' para 'project'.


@app.route('/get_models')
@login_required
def get_models():
    models = []
    with db_connection() as cursor:
        select_query = "SELECT IdModelo, Descripcion FROM Modelo"
        cursor.execute(select_query)
        for row in cursor.fetchall():
            models.append({
                'id': row[0],
                'descripcion': row[1]
            })
    return jsonify(models)


@app.route('/predict', methods=['POST'])
@login_required
def predict():
    # Verificar si el request contiene data en formato json
    global modelid
    global capture_flag
    global modelname
    if request.is_json:
        # Obtener el json del request
        data = request.get_json()
        
        # Extraer la información del json
        modelid = data.get('model')
        capture_flag = data.get('capture')
        modelname = data.get('name')

        # Aquí es donde iría tu lógica para manejar la captura y la predicción.

        # Luego podrías retornar una respuesta en formato json
        
        response = {'message': 'Captura y predicción en proceso.'}
        return jsonify(response), 200

    else:
        return jsonify({'message': 'No se recibió una solicitud en formato JSON.'}), 400
        


     
if __name__ == '__main__':
    app.config['STATIC_FOLDER'] = 'static'
    app.run(host='192.168.43.138', port=8080)
    
