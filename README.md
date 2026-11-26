# Sistema inteligente de detección y mitigación de heladas en cultivos altoandinos

Proyecto desarrollado para el curso **Arquitectura del Computador I** de la Universidad ESAN.

El sistema utiliza una **Raspberry Pi Pico 2 W**, sensores ambientales, procesamiento multinúcleo, conectividad Wi-Fi y una electroválvula de 12 V para detectar condiciones asociadas a heladas y ejecutar automáticamente una acción de mitigación mediante microaspersión.

---

## 1. Problema

Las heladas meteorológicas constituyen un riesgo para los cultivos ubicados en zonas altoandinas del Perú.

El sistema busca monitorear variables ambientales relevantes para detectar oportunamente condiciones de riesgo y reaccionar automáticamente cuando la temperatura del aire alcanza valores correspondientes a una condición de helada.

El objetivo del proyecto no es evitar la aparición de una helada, sino **detectar condiciones críticas y contribuir a mitigar sus efectos sobre los cultivos**.

---

## 2. Objetivo

Diseñar e implementar un sistema embebido capaz de:

- Medir temperatura y humedad del aire.
- Medir intensidad luminosa.
- Medir temperatura del suelo.
- Clasificar las condiciones ambientales.
- Detectar condiciones de riesgo de helada.
- Activar automáticamente una electroválvula.
- Utilizar los dos núcleos de la Raspberry Pi Pico 2 W.
- Conectarse mediante Wi-Fi.
- Enviar telemetría hacia Ubidots.
- Visualizar las mediciones mediante un dashboard.

---

## 3. Arquitectura general

El sistema se divide principalmente en dos bloques de procesamiento.

### Core 0

El Core 0 realiza las tareas críticas del sistema:

- Lectura del SHT31.
- Lectura del BH1750.
- Lectura del DS18B20.
- Procesamiento de las mediciones.
- Clasificación del estado ambiental.
- Control de la electroválvula.
- Actualización de los datos compartidos.

### Core 1

El Core 1 está destinado a las tareas de comunicación y monitoreo:

- Lectura de los datos compartidos.
- Monitoreo de las mediciones.
- Gestión de la conexión Wi-Fi.
- Preparación de los datos para telemetría.
- Envío de información hacia Ubidots mediante HTTP.

La información entre ambos núcleos se comparte mediante una estructura denominada `datos`.

Para evitar accesos simultáneos inconsistentes se utiliza un mecanismo de sincronización mediante `lock`.

```text
SHT31 ──┐
BH1750 ─┼──> CORE 0 ──> Procesamiento ──> Estado
DS18B20 ┘                  │
                           ├──> Electroválvula
                           │
                           └──> Datos compartidos
                                      │
                                    LOCK
                                      │
                                      ▼
                                   CORE 1
                                      │
                                      ▼
                                    Wi-Fi
                                      │
                                      ▼
                                   Ubidots
```

---

## 4. Sensores

### SHT31

Sensor utilizado para medir:

- Temperatura del aire.
- Humedad relativa.

Comunicación:

- I2C.
- Dirección utilizada: `0x44`.

### BH1750

Sensor utilizado para medir:

- Intensidad luminosa en lux.

Comunicación:

- I2C.
- Dirección utilizada: `0x23` o `0x5C`, dependiendo de la configuración del módulo.

### DS18B20

Sensor utilizado para medir:

- Temperatura del suelo.

Comunicación:

- 1-Wire.
- GPIO utilizado: `GP22`.
- Resistencia pull-up: `4.7 kΩ`.

---

## 5. Conexiones principales

### Bus I2C

```text
GP0 → SDA
GP1 → SCL
```

El SHT31 y el BH1750 comparten el mismo bus I2C.

### DS18B20

```text
GP22 → DATA
3.3 V → VDD
GND → GND
```

Se utiliza una resistencia pull-up de `4.7 kΩ` entre DATA y 3.3 V.

### Electroválvula

```text
GP15
  ↓
Resistencia 100 Ω
  ↓
Gate MOSFET
  ↓
MOSFET
  ↓
Electroválvula 12 V
```

También se utiliza:

- Resistencia de `10 kΩ` como pull-down del Gate.
- Diodo `1N4007` como protección flyback.
- Fuente externa de 12 V.
- Tierra común entre el circuito de control y la alimentación de la válvula.

---

## 6. Lógica de funcionamiento

El sistema utiliza tres estados:

### NORMAL

```text
Temperatura del aire > 3 °C
```

Resultado:

```text
Estado: NORMAL
Electroválvula: CERRADA
```

### RIESGO

```text
0 °C < Temperatura del aire <= 3 °C
y
Luz < 100 lux
```

Resultado:

```text
Estado: RIESGO
Electroválvula: CERRADA
```

### HELADA

```text
Temperatura del aire <= 0 °C
```

Resultado:

```text
Estado: HELADA
Electroválvula: ABIERTA
```

La temperatura utilizada para determinar los estados corresponde a la temperatura del aire medida por el **SHT31**.

La temperatura del suelo medida mediante el DS18B20 se utiliza como información adicional de monitoreo.

---

## 7. Control de la electroválvula

La electroválvula es controlada mediante el GPIO `GP15`.

Cuando se detecta una condición de helada:

```python
valvula.value(1)
```

El MOSFET conduce y energiza la electroválvula.

Cuando el sistema se encuentra en NORMAL o RIESGO:

```python
valvula.value(0)
```

La electroválvula permanece cerrada.

También se implementa un comportamiento de seguridad:

Si alguno de los sensores produce una lectura inválida, el sistema coloca:

```text
Estado: ERROR SENSOR
Electroválvula: CERRADA
```

---

## 8. Procesamiento multinúcleo

La Raspberry Pi Pico 2 W permite distribuir las tareas utilizando sus dos núcleos.

El sistema utiliza:

```python
import _thread
```

El segundo núcleo se inicia mediante:

```python
_thread.start_new_thread(core1_comunicaciones, ())
```

Para proteger la información compartida se utiliza:

```python
lock = _thread.allocate_lock()
```

El objetivo es separar las tareas críticas de adquisición y control de las tareas de comunicación y telemetría.

---

## 9. Datos compartidos

La estructura compartida contiene:

```python
datos = {
    "temperatura_aire": 0.0,
    "humedad": 0.0,
    "luz": 0.0,
    "temperatura_suelo": 0.0,
    "estado": "INICIANDO",
    "valvula": "CERRADA"
}
```

Core 0 actualiza estos valores.

Core 1 obtiene una copia de ellos utilizando el mecanismo de sincronización `lock`.

---

## 10. Conectividad Wi-Fi

La Raspberry Pi Pico 2 W se conecta a una red Wi-Fi de **2.4 GHz**.

Durante las pruebas se utilizó un punto de acceso compartido desde una computadora conectada a Internet.

El flujo de conectividad utilizado es:

```text
Internet
   ↓
Red / datos móviles
   ↓
Laptop
   ↓
Hotspot Wi-Fi 2.4 GHz
   ↓
Raspberry Pi Pico 2 W
```

Las credenciales reales de Wi-Fi no deben almacenarse en el repositorio público.

---

## 11. Integración con Ubidots

Se utiliza Ubidots como plataforma de telemetría para visualizar remotamente las mediciones obtenidas por el sistema.

Las variables consideradas son:

```text
temperatura_aire
humedad
luz
temperatura_suelo
estado
valvula
```

Los estados se representan numéricamente de la siguiente manera:

```text
0 → NORMAL
1 → RIESGO
2 → HELADA
```

Para la electroválvula:

```text
0 → CERRADA
1 → ABIERTA
```

Core 1 prepara la información y realiza una solicitud HTTP hacia Ubidots.

La integración completa entre los datos reales de los sensores y el dashboard se encuentra actualmente en proceso de validación.

---

## 12. Dashboard

El dashboard de Ubidots está diseñado para mostrar:

- Temperatura del aire.
- Humedad relativa.
- Intensidad luminosa.
- Temperatura del suelo.
- Estado actual del sistema.
- Estado de la electroválvula.
- Evolución temporal de las temperaturas.

Los widgets utilizados incluyen:

```text
Metric
Indicator
Line Chart
```

---

## 13. Pruebas realizadas

Se han realizado pruebas independientes e integradas de los sensores y del sistema de control.

### Prueba de estado NORMAL

Se verificó que para temperaturas superiores al umbral preventivo:

```text
Estado → NORMAL
Electroválvula → CERRADA
```

### Prueba de estado RIESGO

En una de las pruebas se obtuvieron aproximadamente:

```text
Temperatura del aire: 1.78 °C
Humedad: 61.89 %
Luz: 0.83 lux
Temperatura del suelo: 27.06 °C

Estado: RIESGO
Electroválvula: CERRADA
```

### Prueba de estado HELADA

Se redujo experimentalmente la temperatura medida por el SHT31 hasta alcanzar la condición de helada.

Se verificó:

```text
Estado → HELADA
Electroválvula → ABIERTA
```

---

## 14. Diseño 3D e impresión

Las piezas utilizadas para la integración física del prototipo fueron preparadas mediante **Bambu Studio**.

El formato principal utilizado fue:

```text
3MF
```

Los archivos 3MF contienen los modelos preparados para el proceso de impresión.

También se generaron archivos:

```text
STL
```

como formato adicional para compatibilidad y entrega.

El flujo utilizado fue:

```text
Modelo 3D
   ↓
Bambu Studio
   ↓
Archivo 3MF
   ↓
Preparación y laminado
   ↓
Impresión 3D
```

---

## 15. Estructura del repositorio

```text
proyecto-heladas-pico2w/
│
├── README.md
│
├── src/
│   ├── main.py
│   └── versiones/
│       └── main_sensores_valvula_funcional.py
│
├── diagramas/
│   └── diagrama-conexiones.png
│
├── cad/
│   ├── 3mf/
│   │   └── modelos.3mf
│   └── stl/
│       └── modelos.stl
│
├── evidencias/
│   ├── sensores/
│   ├── dashboard/
│   ├── impresion-3d/
│   └── prototipo-final/
│
└── docs/
```

---

## 16. Seguridad de credenciales

Las credenciales reales del proyecto no deben almacenarse en GitHub.

No se deben publicar:

```text
Contraseña Wi-Fi
TOKEN de Ubidots
API Keys
```

En el código público deben utilizarse valores de ejemplo:

```python
WIFI_SSID = "TU_WIFI"
WIFI_PASSWORD = "TU_PASSWORD"

UBIDOTS_TOKEN = "TU_TOKEN_UBIDOTS"
```

---

## 17. Estado actual del proyecto

```text
Lectura SHT31                         ✅
Lectura BH1750                        ✅
Lectura DS18B20                       ✅
Clasificación NORMAL                  ✅
Clasificación RIESGO                  ✅
Clasificación HELADA                  ✅
Control de electroválvula             ✅
Procesamiento multinúcleo             ✅
Sincronización mediante lock          ✅
Conexión Wi-Fi                        ✅
Configuración de Ubidots              ✅
Dashboard de Ubidots                  ✅
Envío final de telemetría real        🔄 En validación
Diseño / preparación 3D               ✅
Archivos 3MF                          ✅
Archivos STL                          ✅
Integración física final              🔄 En progreso
```

---

## 18. Tecnologías utilizadas

- Raspberry Pi Pico 2 W.
- MicroPython.
- I2C.
- 1-Wire.
- GPIO.
- Procesamiento multinúcleo mediante `_thread`.
- Wi-Fi.
- HTTP.
- JSON.
- Ubidots.
- Bambu Studio.
- Impresión 3D.

---

## 19. Integrantes

- Danitza Anahi Erazo Salvatierra.
- Yeongmi Sayuri Chavez Rivera.

---

## 20. Curso

**Arquitectura del Computador I**

Universidad ESAN  
Facultad de Ingeniería  
2026
