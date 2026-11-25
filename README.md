##Sistema inteligente de detección y mitigación de heladas en cultivos altoandinos
Descripción
Este proyecto propone el desarrollo de un sistema embebido basado en una Raspberry Pi Pico 2 W para monitorear condiciones ambientales relacionadas con la aparición de heladas en cultivos altoandinos.
El sistema utilizará sensores de temperatura, humedad, iluminación y temperatura del suelo para identificar condiciones normales, situaciones de riesgo y eventos de helada.
Además, se plantea controlar una electroválvula conectada a un sistema de microaspersión como mecanismo de mitigación, así como enviar las mediciones mediante Wi-Fi hacia un dashboard para su monitoreo remoto.

Problema
Las heladas pueden producir daños importantes en cultivos ubicados en zonas altoandinas, especialmente durante la noche y madrugada.
La detección tardía de una disminución crítica de temperatura puede impedir una respuesta oportuna.
Por ello, se busca desarrollar un sistema capaz de monitorear continuamente las condiciones ambientales y generar una respuesta automática ante condiciones críticas.

Usuario objetivo
El proyecto está dirigido principalmente a:
·	agricultores de zonas altoandinas;
·	pequeños productores agrícolas;
·	asociaciones y cooperativas agrícolas;
·	instituciones relacionadas con el monitoreo y protección de cultivos.

Objetivo general
Diseñar e implementar un prototipo basado en Raspberry Pi Pico 2 W capaz de monitorear variables ambientales relacionadas con las heladas y ejecutar acciones de alerta y mitigación.

Sensores
SHT31
Sensor de temperatura y humedad del aire.
Protocolo de comunicación:
I2C

BH1750
Sensor de intensidad luminosa.
Protocolo:
I2C

DS18B20
Sensor utilizado para medir la temperatura del suelo.
Protocolo:
1-Wire


Unidad de procesamiento
Se utilizará una:
Raspberry Pi Pico 2 W

La tarjeta será responsable de:
·	leer los sensores;
·	procesar las mediciones;
·	determinar el estado ambiental;
·	controlar los actuadores;
·	conectarse mediante Wi-Fi;
·	enviar información hacia un dashboard.

Actuadores
El sistema utilizará una electroválvula normalmente cerrada de 12 V para controlar el paso de agua hacia un sistema de microaspersión.
La electroválvula será controlada mediante un circuito electrónico de potencia.
También se plantea utilizar un buzzer como sistema de alerta sonora.

Estados del sistema
El prototipo manejará tres estados principales:
NORMAL
RIESGO
HELADA

De manera inicial se propone utilizar la temperatura del aire como variable principal y la iluminación como variable complementaria.

Arquitectura propuesta
SHT31 ──────┐
BH1750 ─────┼──→ Raspberry Pi Pico 2 W
DS18B20 ────┘
                     │
             ┌───────┴────────┐
             │                │
           Core 0           Core 1
             │                │
        Sensores          Wi-Fi
        Procesamiento     Dashboard
        Actuadores        Telemetría
             │                │
             └───────┬────────┘
                     │
                Sistema IoT


Uso de los dos núcleos
El proyecto plantea utilizar los dos núcleos disponibles en la Raspberry Pi Pico 2 W.
Core 0
Se encargará de:
·	lectura de sensores;
·	procesamiento de datos;
·	detección del estado;
·	control de actuadores.
Core 1
Se encargará de:
·	conexión Wi-Fi;
·	envío de datos;
·	comunicación con la plataforma IoT;
·	actualización del dashboard.

Componentes principales
·	Raspberry Pi Pico 2 W
·	SHT31
·	BH1750
·	DS18B20
·	electroválvula de 12 V
·	módulo o MOSFET de control
·	diodo de protección
·	convertidor LM2596
·	fuente de alimentación
·	protoboard
·	resistencias
·	cables de conexión
·	sistema de microaspersión

Funcionamiento esperado
Sensores
   ↓
Lectura de variables
   ↓
Procesamiento
   ↓
Determinación del estado
   ↓
NORMAL / RIESGO / HELADA
   ↓
┌──────────────────┬─────────────────┐
│                  │                 │
Actuador          Alerta           Dashboard
│                                    │
Microaspersión                       Wi-Fi


Tecnologías utilizadas
·	MicroPython
·	Raspberry Pi Pico 2 W
·	I2C
·	1-Wire
·	Wi-Fi
·	HTTP
·	Ubidots
·	Git / GitHub

Estado actual del proyecto
Actualmente el proyecto se encuentra en la etapa inicial de desarrollo.
Se ha definido:
·	problema;
·	usuario objetivo;
·	alcance;
·	sensores;
·	arquitectura propuesta;
·	materiales principales;
·	reto de arquitectura.
Las siguientes etapas consisten en:
1.	probar los sensores individualmente;
2.	integrar los sensores en protoboard;
3.	implementar procesamiento concurrente;
4.	incorporar conectividad Wi-Fi;
5.	enviar datos al dashboard;
6.	integrar actuadores;
7.	realizar pruebas del sistema completo.

Curso
Arquitectura del Computador I
Integrantes
·	Danitza Anahi Erazo Salvatierra Codigo 26102434
·	Yeongmi Milagros Sayuri Chavez Rivera Codigo
Docente
Marks Calderon Niqui
Año
2026
