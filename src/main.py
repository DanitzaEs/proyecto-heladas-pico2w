
            print(
                "Sin Wi-Fi:"
            )

            print(
                "no se enviaron datos a Ubidots"
            )


        time.sleep(5)


_thread.start_new_thread(
    core1_comunicaciones,
    ()
)


print()
print("==============================")
print("     INICIANDO CORE 0")
print("==============================")


while True:


    temperatura_aire, humedad = leer_sht31()

    luz = leer_bh1750()

    temperatura_suelo = leer_ds18b20()


    if (
        temperatura_aire is not None
        and humedad is not None
        and luz is not None
        and temperatura_suelo is not None
    ):


        estado = determinar_estado(

            temperatura_aire,

            luz
        )


        estado_valvula = controlar_valvula(
            estado
        )


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


        valvula.value(0)


        lock.acquire()


        datos[
            "estado"
        ] = "ERROR SENSOR"


        datos[
            "valvula"
        ] = "CERRADA"


        lock.release()


    time.sleep(2)
