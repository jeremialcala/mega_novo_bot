# coding=utf-8
import os
import sys
import json
import requests
import time
import random
import re
import psycopg2
import urlparse
import string
import datetime
from flask import Flask, request
from flask import render_template
from flask import send_file
from elibom.Client import *
from random import randint

app = Flask(__name__)

elibom = ElibomClient('info@novopayment.com', 'X0fAbv3Uu6')
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/termandcond', methods=['GET'])
def termandcond():
    return render_template('index.html')


@app.route('/buttons', methods=['GET'])
def buttons():
    return render_template('buttons.html')


@app.route('/img/hola', methods=['GET'])
def hola():
    filename = '/templates/images/bot-greet.png'
    return send_file(filename, mimetype='image/gif')


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    data = request.get_json()
    # log(data)  # you may not want to log every incoming message in production, but it's good for testing
    phone = "51920058181"  # This is Phone Number"
    token = "654321"  # This is Phone Number"
    if data["object"] == "page":
        for entry in data["entry"]:
            try:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]  # the facebook ID
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID

                    s = json_loads_byteified(get_user_by_id(sender_id))
                    log(s)

                    log(messaging_event["message"])
                    if messaging_event["message"].get("text"):
                        message_text = messaging_event["message"]["text"]
                        if message_text.lower().find("hola") is not -1:
                            msg = "Hola " + s["first_name"] + ", ¿en qué te puedo ayudar?"
                            send_message(sender_id, msg)

                        elif message_text.lower().find("chao") is not -1 or message_text.lower().find(
                                "hasta luego") is not -1 \
                                or message_text.lower().find("gracias") is not -1 \
                                or message_text.lower().find("no") is not -1 \
                                or message_text.lower().find("no acepto") is not -1:

                            msg = "Gracias por su preferencia que tenga un buen dia 👋"
                            send_message(sender_id, msg)

                        elif message_text.lower().find("regist") is not -1:
                            user = get_reg_user_by_id(sender_id)
                            if user is False:
                                msg = "Seguro " + s["first_name"] + ", pero primero nos gustaria que consultaras las " \
                                                                    "condiciones del servicio"
                                send_message(sender_id, msg)
                                time.sleep(3)
                                send_termandc(sender_id)
                                time.sleep(3)
                                msg = "Solo escribe \"Acepto\" para iniciar..."
                                send_message(sender_id, msg)
                            else:
                                msg = "Hey " + s["first_name"] + ", segun parece ya te encuentras registrado"
                                send_message(sender_id, msg)
                                time.sleep(2)
                                msg = "¿deseas realizar alguna otra operación?"
                                send_message(sender_id, msg)
                                time.sleep(2)
                                msg = "puedes consultar tu saldo y movimientos por aca"
                                send_message(sender_id, msg)
                                time.sleep(1)
                                msg = "o tal vez enviar dinero a un amigo..."
                                send_message(sender_id, msg)

                        elif message_text.lower().find("acepto") is not -1:
                            msg = "Gracias " + s["first_name"] + \
                                  ", para continuar ¿me indicas tu numero DNI?"
                            send_message(sender_id, msg)

                        elif message_text.lower().find("saldo") is not -1 \
                                or message_text.lower().find("balance") is not -1:
                            user = get_reg_user_by_id(sender_id)
                            if user is not False:
                                msg = "Tu saldo es S./" + str(user[1])
                                reg_movimientos(sender_id, "CONSULTA DE SALDO", 0.00, user[1], False)
                            else:
                                msg = "Hey " + s["first_name"] + ", segun parece no te encuentras registrado"

                            send_message(sender_id, msg)

                        elif message_text.lower().find("aprobado") is not -1:
                            msg = "Gracias 👍, vamos a procesar tu transferencia"  # + str(random.uniform(1))
                            send_message(sender_id, msg)
                            user = get_reg_user_by_id(sender_id)
                            if user is not False:
                                p2p = get_env_din(sender_id)
                                if p2p is not False:
                                    log(p2p)
                                    reg_movimientos(sender_id, "TRANSFERENCIA TERCEROS TDM", p2p[3], user[1], True)
                                    upd_env_din3(sender_id)
                                time.sleep(5)
                                token = random_with_N_digits(5)
                                send_email('jeremialcala', 'Strolen20',
                                           'dbobadilla@novopayment.com',
                                           'Envio de Dinero',
                                           'Recibiste un envio de dinero de S./ ' + str(p2p[3]) + ', '
                                                                'cobralo en cualquier agente TDM '
                                                                'con el Token: ' + str(token))
                                r = elibom.send_message('51' + str(p2p[2]), 'Recibiste un envio de dinero de S./ ' + str(p2p[3]) + ', '
                                                                'cobralo en cualquier agente TDM '
                                                                'con el Token: ' + str(token))
                                log(r)

                                msg = "envio realizado con éxito, tu amigo ya recibio un SMS con la notificación!"
                                send_message(sender_id, msg)

                                time.sleep(5)
                                msg = "¿Algo mas en lo que te pueda ayudar? 😉"
                                send_message(sender_id, msg)

                        elif message_text.lower().find("movimientos") is not -1 \
                                or message_text.lower().find("operaciones") is not -1:

                            user = get_reg_user_by_id(sender_id)
                            if user is not False:

                                reg_movimientos(sender_id, "CONSULTA DE MOVIMIENTOS", 0.00, user[1], False)
                                msg = "Estos son lo ultimos 3 movimientos que tenemos regitrados en tu cuenta"
                                send_message(sender_id, msg)
                                mov = get_movimientos(sender_id)
                                if len(mov) < 3:
                                    mov.append((sender_id, datetime.datetime.now(), "Sin Movimientos", 0.00, 0.00, 0.00))
                                    mov.append((sender_id, datetime.datetime.now(), "Sin Movimientos", 0.00, 0.00, 0.00))
                                    mov.append((sender_id, datetime.datetime.now(), "Sin Movimientos", 0.00, 0.00, 0.00))

                                show_mov(sender_id, mov)
                            else:
                                msg = "Hey " + s["first_name"] + ", según parece no te encuentras registrado"
                                send_message(sender_id, msg)

                        elif message_text.isdigit() and len(message_text) == 9:
                            user = get_reg_user_by_id(sender_id)
                            if user is not False:
                                msg = "Ok... ¿me indicas el monto a enviar (ej. 5.99)?"
                                upd_env_din1(sender_id, message_text)
                                send_message(sender_id, msg)

                            else:
                                msg = "Hey " + s["first_name"] + ", según parece no te encuentras registrado"
                                send_message(sender_id, msg)

                        elif message_text.lower().find(".") is not -1 and len(message_text) == 4:
                            user = get_reg_user_by_id(sender_id)
                            if user is not False:
                                msg = "Listo👍, para confirmar el envio solo escribe \"Aprobado\"?"
                                send_message(sender_id, msg)
                                upd_env_din2(sender_id, message_text)
                                log("Saldo: " + user[1])
                                log("Monto: " + message_text)
                                #if user[1] > message_text:

                                #else:
                                #    msg = "No dispones del saldo Suficiente para realizar esta operación"
                                #    send_message(sender_id, msg)
                            else:
                                msg = "Hey " + s["first_name"] + ", según parece no te encuentras registrado"
                                send_message(sender_id, msg)

                        elif message_text.lower().find("9") is not -1 and len(message_text) == 8:
                            msg = "Ok... ¿me indicas tu numero Celular Movistar?"
                            send_message(sender_id, msg)

                        elif message_text.isdigit() and message_text.lower().find("519") is not -1 \
                                and len(message_text) == 11:
                            msg = " Gracias vamos a iniciar el proceso de Afiliación..."
                            send_message(sender_id, msg)
                            time.sleep(4)
                            autoafiliacion(sender_id, msg)
                            token = random_with_N_digits(6)
                            send_email('jeremialcala', 'Strolen20', 'dbobadilla@novopayment.com', 'Clave de Confirmacion',
                                       'Bienvenido a Tu Dinero Movil, confirma tu registro '
                                                                  'con el Token: ' + str(token))
                            log("MSISDN: " + message_text)
                            log(token)
                            r = elibom.send_message(message_text, 'Bienvenido a Tu Dinero Movil, '
                                                                  'confirma tu registro '
                                                                  'con el Token: ' + str(token))
                            log(r)
                            reg_token_aut(sender_id, token, message_text)
                            msg = "te enviamos una clave de confirmación a tu número celular."
                            send_message(sender_id, msg)
                            time.sleep(3)
                            msg = "¿me la indicas?, por favor"
                            send_message(sender_id, msg)

                        elif message_text.isdigit() and len(message_text) == 6:

                            token = get_token_aut(sender_id)
                            log(token[1])
                            if token is False:
                                msg = "No tenemos ningun token Registrado"
                                send_message(sender_id, msg)
                            else:
                                if token[0] == message_text:
                                    is_reg = get_reg_user_by_id(sender_id)
                                    log(is_reg)
                                    if is_reg is False:
                                        reg_user_fb(sender_id, token[1])
                                        upd_token_aut(sender_id)
                                        time.sleep(4)
                                        mpin = random_with_N_digits(4)
                                        send_email('jeremialcala', 'Strolen20',
                                                   'dbobadilla@novopayment.com',
                                                   'Clave MPIN',
                                                   'Bienvenido a Tu Dinero Movil, Usuario Registrado '
                                                                          'clave MPIN: ' + str(mpin))
                                        msg = "Muchas Gracias por registrarte ☺, en breve te enviaremos un SMS con tu clave MPIN"
                                        send_message(sender_id, msg)
                                        r = elibom.send_message(token[1], 'Bienvenido a Tu Dinero Movil, '
                                                                          'Usuario Registrado '
                                                                          'clave MPIN: ' + str(mpin))
                                        log(r)
                                        time.sleep(4)
                                        msg = "por registrarte por este canal tienes un bono de S./ 10.00"
                                        send_message(sender_id, msg)
                                        time.sleep(2)
                                        user = get_reg_user_by_id(sender_id)
                                        msg = "Tu saldo es S./" + str(user[1])
                                        send_message(sender_id, msg)
                                        time.sleep(2)
                                        msg = "¿Algo mas en lo que te pueda ayudar? 😉"
                                        send_message(sender_id, msg)
                                else:
                                    msg = "Token no coincide con el Registrado, ¿indicame nuevamente el numero?"
                                    send_message(sender_id, msg)

                        elif message_text.lower().find("enviar dinero a ") is not -1 \
                                or message_text.lower().find("envio de dinero a ") is not -1 \
                                or message_text.lower().find("transferir dinero a ") is not -1 \
                                or message_text.lower().find("transferencia a ") is not -1 \
                                or message_text.lower().find("transferir a ") is not -1:

                            user = get_reg_user_by_id(sender_id)
                            if user is not False:
                                msg = "Muy bien, permiteme buscar a la persona"
                                nombres = message_text.split(' a ')
                                if len(nombres)<= 1:
                                    nombres = message_text.split(' A ')

                                log(nombres[1])
                                send_message(sender_id, msg)
                                reg_env_din(sender_id, nombres[1])
                                time.sleep(3)

                                if message_text.lower().find("Jeremi") is not -1:
                                    show_profile(sender_id, "1102180486547827")
                                    msg = "Indicame el monto (ej. 5.99)"
                                    send_message(sender_id, msg)
                                else:
                                    msg = "Al parecer no lo tengo registrado..."
                                    send_message(sender_id, msg)

                                    msg = "indicame el número de celular (ej. 963605271)"
                                    send_message(sender_id, msg)
                                    # show_profile(sender_id, sender_id)
                            else:
                                msg = "Hey " + s["first_name"] + ", según parece no te encuentras registrado"
                                send_message(sender_id, msg)

                        elif message_text.lower().find("preafi") is not -1:

                            preafiliacion(sender_id, '5196305071')

                        elif message_text.lower().find("ayuda") is not -1 or message_text.lower().find(
                            "asistencia") is not -1 \
                            or message_text.lower().find("duda") is not -1:

                            show_help(sender_id)

                        else:
                            show_what(sender_id)

            except KeyError as e:
                log(e.message)
            except AttributeError as e:
                log(e.message)
            except TypeError as e:
                log(str(e))

    return "ok", 200


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def get_reg_user_by_id(user_id):
    log(user_id)
    sql = "SELECT * FROM USER_FB WHERE FB_ID_MSG = '" + str(user_id) + "';"
    # log(sql)
    cur.execute(sql)
    rows = cur.fetchall()
    log(rows)
    if len(rows) > 0:
        return rows[0][1], rows[0][4]
    else:
        return False


def reg_env_din(user_id, dest):
    try:
        log("Registrando usuario")
        cur.execute("""INSERT INTO ENVIO_DINERO(FB_ID, NOMBRE, PENDIENTE) VALUES(%s, %s, TRUE);""",
                    (user_id, dest))
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def upd_env_din1(user_id, msisdn):
    try:
        log("Registrando MSISDN Destino")
        sql = "UPDATE ENVIO_DINERO SET MSISDN_RCP='" + msisdn + "' WHERE FB_ID= '" + user_id + "' and PENDIENTE = TRUE;"
        cur.execute(sql)
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def upd_env_din2(user_id, monto):
    try:
        log("Registrando MSISDN Destino")
        sql = "UPDATE ENVIO_DINERO SET MONTO='" + monto + "' WHERE FB_ID= '" + user_id + "' and PENDIENTE = TRUE;"
        cur.execute(sql)
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def upd_env_din3(user_id):
    try:
        log("Cambiendo estado del envio de dinero")
        sql = "UPDATE ENVIO_DINERO SET PENDIENTE = FALSE WHERE FB_ID= '" + user_id + "' and PENDIENTE = TRUE;"
        cur.execute(sql)
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def get_env_din(user_id):
    try:
        log("Buscando envio de dinero")
        sql = "SELECT * FROM ENVIO_DINERO WHERE FB_ID = '" + user_id + "' AND PENDIENTE = TRUE;"
        cur.execute(sql)
        rows = cur.fetchone()
        log(rows)
        if len(rows) > 0:
            return rows
        else:
            return False
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def reg_user_fb(user_id, msisdn):
    try:
        log("Registrando usuario")
        log(msisdn)
        cur.execute("""INSERT INTO USER_FB(FB_ID_MSG, MSISDN, SALDO) VALUES(%s, %s, 0.00);""",
                    (user_id, msisdn))
        conn.commit()
        reg_movimientos(user_id, "DEPOSITO PROMO REGISTRO FB", 10.00, 0.00, False)
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def reg_token_aut(user_id, TOKEN, msisdn):
    try:
        cur.execute("""INSERT INTO TOKEN_AUTAFI(FB_ID, TOKEN, MSISDN, USADO) VALUES(%s, %s, %s, FALSE);""",
                    (user_id, TOKEN, msisdn))
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def upd_token_aut(user_id):
    try:
        sql = "UPDATE TOKEN_AUTAFI SET USADO = TRUE WHERE FB_ID = '" + str(user_id) + "';"
        cur.execute(sql)
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def get_token_aut(user_id):
    sql = "SELECT TOKEN, MSISDN FROM TOKEN_AUTAFI WHERE FB_ID = '" + str(user_id) + "' AND USADO = FALSE;"
    log(sql)
    cur.execute(sql)
    rows = cur.fetchall()
    log(rows)
    if len(rows) > 0:
        return rows[0][0], rows[0][1]
    else:
        return False


def reg_movimientos(user_id, descr, monto, saldo, debito):
    log("Registrando movimiento " + str(monto))
    saldo_fin = saldo
    if monto != 0.0:
        log(monto)
        if debito:
            saldo_fin = saldo - monto
        else:
            saldo_fin = saldo + monto
    try:
        cur.execute("""INSERT INTO MOV_USER(FB_ID, DESCRIP, MONTO, SALDO_ANT, SALDO_FIN)
                VALUES(%s, %s, %s, %s, %s);""", (user_id, descr, monto, saldo, saldo_fin))
        sql = "UPDATE USER_FB SET SALDO= " + str(saldo_fin) +" WHERE FB_ID_MSG = '" + str(user_id) + "';"
        log(sql)
        cur.execute(sql)
        conn.commit()
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def get_movimientos(user_id):
    try:
        sql = "SELECT * FROM MOV_USER WHERE FB_ID = '" + str(user_id) + "' ORDER BY FECHA DESC LIMIT 3;"
        cur.execute(sql)
        rows = cur.fetchall()
        log(rows)
        return rows
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        log(e)


def get_user_by_id(user_id):
    url = "https://graph.facebook.com/USER_ID?&access_token="
    url = url.replace("USER_ID", user_id) + os.environ["PAGE_ACCESS_TOKEN"]
    # log(url)
    r = requests.get(url)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return r.status_code, r.text
    else:
        return r.text


def find_user_by_name(name):
    url = "https://graph.facebook.com/search?q=USER_NAME&limit=1&offset=0&type=user&format=json&access_token="
    url = url.replace("USER_NAME", name) + os.environ["PAGE_ACCESS_TOKEN"]
    # log(url)
    r = requests.get(url)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return r.status_code, r.text
    else:
        return r.text


def getSaldo(sender_id):
    url = "http://72.46.255.110:8005/facebook-service/1.0/user/balance/" + sender_id

    r = requests.get(url)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return r.status_code, r.text
    else:
        return r.text


def autoafiliacion(sender_id, token):
    headers = {
        "Content - Type": "application / json",
        "x - country": "Pe"
    }

    data = {
        "idOperation": "108",
        "bean": token,
        "facebookId": sender_id
    }

    log(data)
    r = requests.post("http://72.46.255.110:8005/facebook-service/1.0/user/auto-afiliation", headers=headers, data=data)
    log(r)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def preafiliacion(sender_id, msisdn):
    headers = {
        "Content-Type": "application/json",
        "x-country": "Pe"
    }

    data = {
            "bean": "{\"usuarioMsisdn\":\"51963605071\",\"primer_nombre\":\"Gustavo\",\"segundo_nombre\":\"Adolfo\",\"primer_apellido\":\"Mora\",\"segundo_apellido\":\"Pereda\",\"fecha_nacimiento\":\"01-12-1992\",\"dni\":\"20801243\",\"sexo\":\"M\",\"email\":\"gmora922@gmail.com\",\"id_civil\":\"S\"}",
            "facebookId": "1"
        }


    log(data)
    r = requests.post("http://72.46.255.110:8005/facebook-service/1.0/user/pre-afiliation", headers=headers, data=data)

    log(r)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_termandc(recipient_id):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        }, "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Tu Dinero Móvil",
                            "subtitle": "Terminos y Condiciones del Servicio",
                            "buttons": [
                                {
                                    "type": "web_url",
                                    "url": "http://www.tudineromovil.pe/wp-content/themes/np-tdm/media/documents/contrato_cuenta_simplificada_201606.pdf",
                                    "title": "+ info"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    })
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def show_profile(recipient_id, user_id):
    r = json_loads_byteified(get_user_by_id(user_id))
    nombres = r["first_name"] + " " + r["last_name"]

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        }, "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Deseas enviarle dinero a: ",
                            "subtitle": nombres,
                            "image_url": r["profile_pic"]

                        }
                    ]
                }
            }
        }
    })
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def show_what(recipient_id):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        }, "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Vamos a consultar tu solicitud en breve ",
                            "subtitle": " por favor espere 😇",
                            "image_url": "http://www.latodo.pe/wp-content/uploads/bot-what.png"
                        }
                    ]
                }
            }
        }
    })
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def show_mov(recipient_id, movs):
    log("Ingresando a Show_MOV")
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    log(movs)
    lista = ""

    # for mov in movs:
    # lista += {'title': mov[2], 'subtitle': mov[3]}

    # log(lista)
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        }, "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    "top_element_style": "compact",
                    "elements": [
                        {
                            "title": movs[0][2],
                            "image_url": "https://peterssendreceiveapp.ngrok.io/img/collection.png",
                            "subtitle": movs[0][1].strftime('%y.%m.%d %H:%M - ') +
                                        str(movs[0][3])
                        },
                        {
                            "title": movs[1][2],
                            "image_url": "https://peterssendreceiveapp.ngrok.io/img/collection.png",
                            "subtitle": movs[1][1].strftime('%y.%m.%d %H:%M - ') +
                                        str(movs[1][3])
                        },
                        {
                            "title": movs[2][2],
                            "image_url": "https://peterssendreceiveapp.ngrok.io/img/collection.png",
                            "subtitle": movs[2][1].strftime('%y.%m.%d %H:%M - ') +
                                        str(movs[2][3])
                        }
                    ],
                    "buttons": []
                }
            }
        }
    })
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def show_help(recipient_id):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        }, "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Para mayor asistencia e información contáctenos al: ",
                            "subtitle": "0800-100-122",
                            "image_url": "http://www.latodo.pe/wp-content/uploads/bot-contact.png"
                        }
                    ]
                }
            }
        }
    })
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_email(user, pwd, recipient, subject, body):
    import smtplib

    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(change_text(message))
    sys.stdout.flush()


def change_text(text):
    return text.encode('utf-8')


def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
            }
    # if it's anything else, return it in its original form
    return data


if __name__ == '__main__':
    app.run(debug=True)
