# Contenido base de la presentación

Guion para la presentación de resultados. La idea es **contar la historia del
análisis**, no mostrar código. Cada diapositiva indica la figura que la acompaña y
el mensaje que debe quedar.

---

## 1. Título

**A Step Ahead of Drought: pronóstico global de almacenamiento de agua**
Proyecto 2 — Análisis Exploratorio · CC3084 Data Science · UVG · Semestre II 2026
Integrantes: *(completar)*

---

## 2. Contexto del problema

*Figura: `figures/18_mapa_promedio.png`*

- El **TWS (Total Water Storage)** es toda el agua sobre y bajo la superficie:
  subterránea, humedad del suelo, superficial, nieve y hielo.
- Las misiones satelitales **GRACE y GRACE-FO** lo estiman midiendo variaciones del
  campo gravitatorio terrestre.
- Es el mejor indicador integrado de **sequía hidrológica** a gran escala.

> **Mensaje:** medimos el agua del planeta pesándolo desde el espacio.

---

## 3. Problema científico y objetivos

- **El problema:** los productos GRACE se publican con **2 a 3 meses de retraso**.
  Para alerta temprana necesitamos el estado actual, y tenemos el de hace un
  trimestre.
- **El reto:** predecir el TWS del mes siguiente. Métrica: RMSE.
- **Pregunta científica:** ¿qué patrones temporales, estacionales y espaciales
  presenta el TWS, y qué variables se asocian más con el mes siguiente?

> **Mensaje:** la información existe, pero llega tarde para decidir.

---

## 4. Descripción del dataset

- **2 154 021** observaciones de entrenamiento · **280 961** de prueba · 13 variables
- Rejilla global de **1°**, con **15 715 celdas**, de −55.5° a 83.5° de latitud
- Periodo: **mayo 2002 – agosto 2015** (138 meses observados)
- Variables: `TWS_t`, `SPEI` a 1/3/6/12 meses, `SOIL_MOISTURE_t`, `target`
- **Todas estandarizadas y adimensionales**: no son centímetros de agua

> **Mensaje:** una fila por mes y por celda del planeta.

---

## 5. Calidad y limpieza de los datos

*Figura: `figures/10_cobertura_temporal.png`*

- **Cero nulos, cero duplicados.** Pero eso engaña.
- El formato es plano: si un mes no se observó, **no genera filas** en vez de
  generar `NaN`.
- Faltan **22 de los 160 meses** del calendario (13.8 %), concentrados en
  2002–2003 y 2011–2014. Los años 2004–2010 están completos.
- **Atípicos:** 0.25 % en `target`, 2.58 % en humedad del suelo.
  **No se eliminaron**: se agrupan en años y regiones concretos, firma de eventos
  hidrológicos reales, y son justamente lo que el reto busca anticipar.

> **Mensaje:** el `isna().sum()` daba cero y aun así faltaba el 14 % del periodo.

---

## 6. Patrones temporales

*Figura: `figures/16_media_movil.png`*

- **Tendencia descendente sostenida**: el promedio anual cae de **0.322 en 2004** a
  **−0.136 en 2015**.
- La serie **no es estacionaria** en media (Dickey-Fuller, p = 0.526).
- La descomposición atribuye **64 % de la varianza a la tendencia** y solo **3 % al
  ciclo anual**.
- El resultado no depende de la agregación: promedio simple y ponderado por área
  correlacionan **0.936**.

> **Mensaje:** el planeta se está secando en el registro, y la serie tiene memoria
> larga.

---

## 7. La estacionalidad que casi no vemos

*Figura: `figures/17_perfil_estacional.png`*

- A primera vista **no hay estacionalidad**: solo el 3 % de la varianza.
- La causa: los hemisferios tienen ciclos **opuestos**. El norte promedia positivo
  los 12 meses; el sur cae hasta −0.105 en junio. **Se cancelan al promediarse.**
- Además el conjunto está desbalanceado: **80.3 % de las celdas están en el norte**.
- Al separar por banda de latitud, el ciclo anual **reaparece con claridad**.

> **Mensaje:** promediar el planeta entero borra el fenómeno. Hay que mirar por
> región.

---

## 8. Relaciones entre variables

*Figuras: `figures/19_matriz_correlacion.png` y `figures/20_dispersion_objetivo.png`*

| Variable | Correlación con `target` |
| --- | ---: |
| `TWS_t` (persistencia) | **0.803** |
| `SPEI_12_t` | 0.380 |
| `SPEI_06_t` | 0.368 |
| `SOIL_MOISTURE_t` | 0.320 |
| `SPEI_03_t` | 0.285 |
| `SPEI_01_t` | 0.204 |

- **La persistencia domina**: el mejor predictor del mes siguiente es el mes actual.
- Los SPEI se ordenan **exactamente por escala de acumulación**: a mayor periodo
  acumulado, mayor asociación. Coherente con que el TWS integra agua subterránea,
  de respuesta lenta.
- Relaciones **lineales**: Pearson y Spearman difieren ≤ 0.024.

> **Mensaje:** el agua tiene inercia, y la sequía de largo plazo importa más que la
> del mes pasado.
>
> *Cuidado:* esto es **asociación**, no causalidad.

---

## 9. Hallazgos más importantes

1. Sin nulos ni duplicados, pero **faltan 22 meses completos** del calendario.
2. `target` es el TWS del mes calendario `t+1` — verificado celda por celda.
3. Las variables están **estandarizadas**; no admiten lectura como volumen físico.
4. **Tendencia descendente** y serie no estacionaria.
5. La **estacionalidad se cancela** globalmente pero existe por región.
6. Fuerte **desbalance espacial** (80 % hemisferio norte); las regiones difieren de
   −0.222 a 0.327.
7. **Persistencia dominante** (r = 0.803).
8. **Línea base a superar: RMSE 0.5724.**

---

## 10. Conclusiones y próximos pasos

**Conclusiones**

- El problema de calidad no son los nulos, es la **cobertura del calendario**.
- El **promedio global no es representativo**: hay que analizar por región.
- La **inercia del sistema** es la señal más fuerte disponible.
- El análisis es **descriptivo y asociativo**; no se establece causalidad.

**Próximos pasos**

1. Reportar siempre contra la **línea base de persistencia (RMSE 0.5724)**.
2. Construir rezagos **respetando los meses ausentes** (un `shift()` ingenuo
   produciría rezagos falsos).
3. Incorporar la **dimensión regional** y validar por regiones.
4. **Tratar la tendencia** explícitamente: diferenciar o modelar.
5. Priorizar **`SPEI_12_t` y `SPEI_06_t`**.
6. Validación **cronológica**, nunca aleatoria.
7. Manejar el **enmascaramiento del 66.53 %** de `TWS_t` en el conjunto de prueba,
   que es justamente la variable más predictiva.
