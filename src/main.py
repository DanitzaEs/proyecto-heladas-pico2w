from machine import Pin, I2C
import onewire
import ds18x20
import time
import _thread
import network
import urequests
import json
import gc


# ============================================================
# WIFI
# ============================================================

# IMPORTANTE:
# Estos son los datos del HOTSPOT DE LA LAPTOP
# al que ya lograste conectar la Pico.

WIFI_SSID = "DESKTOP-PR5S9E8 0222"
WIFI_PASSWORD = ">7031uP3"


# ============================================================
# UBIDOTS
# ============================================================

# Usa un TOKEN NUEVO.
UBIDOTS_TOKEN = "BBUS-Kbgzm44nKkM1hGV1Eu4pIXUB34Yv8o"

# Debe ser exactamente el LABEL del dispositivo en Ubidots.
DEVICE_LABEL = "sistema-heladas"

UBIDOTS_URL = (
    "https://industrial.api.ubidots.com"
    "/api/v1.6/devices/"
    + DEVICE_LABEL
    + "/"
)


# ============================================================
# I2C
# SHT31 + BH1750
# ============================================================

i2c = I2C(
    0,
    sda=Pin(0),
    scl=Pin(1),
    freq=100000
)

SHT31_ADDR = 0x44


print("Escaneando dispositivos I2C...")

dispositivos_i2c = i2c.scan()

for dispositivo in dispositivos_i2c:
    print("Encontrado:", hex(dispositivo))


# Detectar automaticamente BH1750

if 0x23 in dispositivos_i2c:

    BH1750_ADDR = 0x23

elif 0x5C in dispositivos_i2c:

    BH1750_ADDR = 0x5C

else:

    BH1750_ADDR = None
    print("BH1750 no encontrado")


# ============================================================
# DS18B20
# ============================================================

onewire_bus = onewire.OneWire(Pin(22))

ds18b20 = ds18x20.DS18X20(
    onewire_bus
)

sensores_ds = ds18b20.scan()


if len(sensores_ds) > 0:

    print("DS18B20 encontrado")

else:

    print("DS18B20 NO encontrado")


# ============================================================
# ELECTROVALVULA
# ============================================================

valvula = Pin(
    15,
    Pin.OUT
)

# Seguridad:
# comienza cerrada
valvula.value(0)


# ============================================================
# DATOS COMPARTIDOS
# CORE 0 <-> CORE 1
# ============================================================

datos = {

    "temperatura_aire": 0.0,

    "humedad": 0.0,

    "luz": 0.0,

    "temperatura_suelo": 0.0,

    "estado": "INICIANDO",

    "valvula": "CERRADA"
}


# Evita que los dos cores modifiquen/lean
# los datos al mismo tiempo.

lock = _thread.allocate_lock()


# ============================================================
# FUNCION SHT31
# ============================================================

def leer_sht31():

    try:

        i2c.writeto(
            SHT31_ADDR,
            bytes([0x24, 0x00])
        )

        time.sleep_ms(20)


        datos_sensor = i2c.readfrom(
            SHT31_ADDR,
            6
        )


        temp_raw = (
            datos_sensor[0] << 8
        ) | datos_sensor[1]


        temperatura = (
            -45
            + (175 * temp_raw / 65535)
        )


        hum_raw = (
            datos_sensor[3] << 8
        ) | datos_sensor[4]


        humedad = (
            100 * hum_raw / 65535
        )


        return temperatura, humedad


    except Exception as error:

        print(
            "Error SHT31:",
            error
        )

        return None, None


# ============================================================
# FUNCION BH1750
# ============================================================

def leer_bh1750():

    if BH1750_ADDR is None:

        return None


    try:

        i2c.writeto(
            BH1750_ADDR,
            bytes([0x10])
        )

        time.sleep_ms(180)


        datos_sensor = i2c.readfrom(
            BH1750_ADDR,
            2
        )


        valor = (
            datos_sensor[0] << 8
        ) | datos_sensor[1]


        lux = valor / 1.2


        return lux


    except Exception as error:

        print(
            "Error BH1750:",
            error
        )

        return None


# ============================================================
# FUNCION DS18B20
# ============================================================

def leer_ds18b20():

    if len(sensores_ds) == 0:

        return None


    try:

        ds18b20.convert_temp()

        time.sleep_ms(750)


        temperatura = ds18b20.read_temp(
            sensores_ds[0]
        )


        return temperatura


    except Exception as error:

        print(
            "Error DS18B20:",
            error
        )

        return None


# ============================================================
# CLASIFICACION
# ============================================================

def determinar_estado(
    temperatura,
    luz
):

    if temperatura <= 0:

        return "HELADA"


    elif (
        temperatura <= 3
        and luz < 100
    ):

        return "RIESGO"


    else:

        return "NORMAL"


# ============================================================
# ELECTROVALVULA
# ============================================================

def controlar_valvula(
    estado
):

    if estado == "HELADA":

        # GP15 HIGH
        # MOSFET conduce
        # electroválvula abre

        valvula.value(1)

        return "ABIERTA"


    else:

        # GP15 LOW
        # electroválvula cerrada

        valvula.value(0)

        return "CERRADA"


# ============================================================
# CONECTAR WIFI
# ESTA FUNCION SE UTILIZA DESDE CORE 1
# ============================================================

def conectar_wifi(
    wlan
):

    if wlan.isconnected():

        print(
            "Wi-Fi ya conectado"
        )

        print(
            "IP:",
            wlan.ifconfig()[0]
        )

        return True


    print()
    print(
        "CORE 1: conectando al Wi-Fi..."
    )


    wlan.active(True)


    # Limpiar intento anterior

    try:

        wlan.disconnect()

    except:

        pass


    time.sleep(1)


    wlan.connect(
        WIFI_SSID,
        WIFI_PASSWORD
    )


    for intento in range(20):

        estado_wifi = wlan.status()


        print(
            "Wi-Fi intento:",
            intento + 1,
            "| estado:",
            estado_wifi
        )


        if wlan.isconnected():

            print()
            print(
                "Wi-Fi CONECTADO"
            )

            print(
                "IP:",
                wlan.ifconfig()[0]
            )

            return True


        # Estado negativo = error

        if estado_wifi < 0:

            print(
                "Error de conexion Wi-Fi:",
                estado_wifi
            )

            return False


        time.sleep(1)


    print(
        "Tiempo de conexion agotado"
    )

    return False


# ============================================================
# CONVERTIR ESTADOS PARA UBIDOTS
# ============================================================

def convertir_estado(
    estado
):

    if estado == "NORMAL":

        return 0


    elif estado == "RIESGO":

        return 1


    elif estado == "HELADA":

        return 2


    else:

        return -1


def convertir_valvula(
    estado_valvula
):

    if estado_valvula == "ABIERTA":

        return 1

    else:

        return 0


# ============================================================
# ENVIAR A UBIDOTS
# ============================================================

def enviar_a_ubidots(
    temperatura_aire,
    humedad,
    luz,
    temperatura_suelo,
    estado,
    estado_valvula
):

    estado_num = convertir_estado(
        estado
    )


    valvula_num = convertir_valvula(
        estado_valvula
    )


    # --------------------------------------------------------
    # JSON QUE RECIBIRA UBIDOTS
    # --------------------------------------------------------

    payload = {

        "temperatura_aire":
            temperatura_aire,

        "humedad":
            humedad,

        "luz":
            luz,

        "temperatura_suelo":
            temperatura_suelo,

        "estado": {

            "value":
                estado_num,

            "context": {

                "nombre":
                    estado
            }
        },

        "valvula": {

            "value":
                valvula_num,

            "context": {

                "nombre":
                    estado_valvula
            }
        }
    }


    headers = {

        "X-Auth-Token":
            UBIDOTS_TOKEN,

        "Content-Type":
            "application/json"
    }


    respuesta = None


    try:

        # Liberar un poco de memoria
        # antes de la solicitud HTTPS.

        gc.collect()


        print()
        print(
            "Enviando a Ubidots..."
        )


        respuesta = urequests.post(

            UBIDOTS_URL,

            headers=headers,

            data=json.dumps(
                payload
            )
        )


        print(
            "Respuesta Ubidots:",
            respuesta.status_code
        )


        # 200 = solicitud aceptada

        if respuesta.status_code == 200:

            print(
                "Datos enviados correctamente"
            )

        else:

            print(
                "Ubidots respondio con error"
            )


        respuesta.close()

        return True


    except Exception as error:

        print(
            "ERROR UBIDOTS:",
            error
        )


        if respuesta is not None:

            try:

                respuesta.close()

            except:

                pass


        return False


# ============================================================
# CORE 1
#
# RESPONSABILIDAD:
# - Wi-Fi
# - leer datos compartidos
# - mostrar monitoreo
# - enviar datos a Ubidots
# ============================================================

def core1_comunicaciones():

    print()
    print("==============================")
    print("     INICIANDO CORE 1")
    print("==============================")


    # --------------------------------------------------------
    # LA INTERFAZ WIFI SE CREA EN CORE 1
    # --------------------------------------------------------

    wlan = network.WLAN(
        network.STA_IF
    )


    # Primer intento de conexión

    conectar_wifi(
        wlan
    )


    while True:


        # ====================================================
        # COPIAR DATOS COMPARTIDOS
        # ====================================================

        lock.acquire()


        temperatura_aire = datos[
            "temperatura_aire"
        ]

        humedad = datos[
            "humedad"
        ]

        luz = datos[
            "luz"
        ]

        temperatura_suelo = datos[
            "temperatura_suelo"
        ]

        estado = datos[
            "estado"
        ]

        estado_valvula = datos[
            "valvula"
        ]


        lock.release()


        # ====================================================
        # MOSTRAR INFORMACION
        # ====================================================

        print()
        print(
            "================================"
        )

        print(
            "       CORE 1 - MONITOREO"
        )

        print(
            "================================"
        )


        print(
            "Temperatura aire:",
            temperatura_aire,
            "C"
        )


        print(
            "Humedad:",
            humedad,
            "%"
        )


        print(
            "Luz:",
            luz,
            "lux"
        )


        print(
            "Temperatura suelo:",
            temperatura_suelo,
            "C"
        )


        print(
            "Estado:",
            estado
        )


        print(
            "Electrovalvula:",
            estado_valvula
        )


        print(
            "================================"
        )


        # ====================================================
        # NO ENVIAR LOS CEROS DE INICIO
        # ====================================================

        if estado == "INICIANDO":

            print(
                "Esperando primera lectura..."
            )

            time.sleep(2)

            continue


        # ====================================================
        # COMPROBAR WIFI
        # ====================================================

        if not wlan.isconnected():

            print(
                "Wi-Fi desconectado."
            )

            print(
                "Intentando reconectar..."
            )


            conectar_wifi(
                wlan
            )


        # ====================================================
        # ENVIAR A UBIDOTS
        # ====================================================

        if wlan.isconnected():

            enviar_a_ubidots(

                temperatura_aire,

                humedad,

                luz,

                temperatura_suelo,

                estado,

                estado_valvula
            )


        else:

            print(
                "Sin Wi-Fi:"
            )

            print(
                "no se enviaron datos a Ubidots"
            )


        # ----------------------------------------------------
        # Ubidots se actualiza cada 5 segundos
        # ----------------------------------------------------

        time.sleep(5)


# ============================================================
# INICIAR CORE 1
# ============================================================

_thread.start_new_thread(
    core1_comunicaciones,
    ()
)


# ============================================================
# CORE 0
#
# RESPONSABILIDAD:
# - leer sensores
# - procesar datos
# - clasificar estado
# - controlar electroválvula
# - actualizar datos compartidos
# ============================================================

print()
print("==============================")
print("     INICIANDO CORE 0")
print("==============================")


while True:


    # --------------------------------------------------------
    # LEER SENSORES
    # --------------------------------------------------------

    temperatura_aire, humedad = leer_sht31()

    luz = leer_bh1750()

    temperatura_suelo = leer_ds18b20()


    # --------------------------------------------------------
    # COMPROBAR LECTURAS
    # --------------------------------------------------------

    if (
        temperatura_aire is not None
        and humedad is not None
        and luz is not None
        and temperatura_suelo is not None
    ):


        # ----------------------------------------------------
        # CLASIFICACION
        # ----------------------------------------------------

        estado = determinar_estado(

            temperatura_aire,

            luz
        )


        # ----------------------------------------------------
        # ELECTROVALVULA
        # ----------------------------------------------------

        estado_valvula = controlar_valvula(
            estado
        )


        # ----------------------------------------------------
        # ACTUALIZAR DATOS COMPARTIDOS
        # ----------------------------------------------------

        lock.acquire()


        datos[
            "temperatura_aire"
        ] = round(
            temperatura_aire,
            2
        )


        datos[
            "humedad"
        ] = round(
            humedad,
            2
        )


        datos[
            "luz"
        ] = round(
            luz,
            2
        )


        datos[
            "temperatura_suelo"
        ] = round(
            temperatura_suelo,
            2
        )


        datos[
            "estado"
        ] = estado


        datos[
            "valvula"
        ] = estado_valvula


        lock.release()


    else:


        # ====================================================
        # FAIL-SAFE
        # ====================================================

        # Si falla un sensor:
        # cerrar válvula.

        valvula.value(0)


        lock.acquire()


        datos[
            "estado"
        ] = "ERROR SENSOR"


        datos[
            "valvula"
        ] = "CERRADA"


        lock.release()


    # Core 0 actualiza sensores
    # cada 2 segundos.

    time.sleep(2)
