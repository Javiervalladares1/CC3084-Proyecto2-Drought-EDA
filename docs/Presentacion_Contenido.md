# Guion de la presentación

Presentación de resultados del Proyecto 2, diseñada para **15 minutos** repartidos
entre cuatro expositores. El archivo `Proyecto2_Presentacion.pptx` lleva estas
mismas notas dentro de cada diapositiva, en el panel de notas del orador.

El contenido escrito suma **14:45**, lo que deja margen para las transiciones entre
expositores. En la práctica casi siempre se va uno por encima, así que conviene
cronometrar el primer ensayo completo y recortar donde haga falta.

## Reparto y tiempos

| Bloque | Expositor | Diapositivas | Tiempo |
| ------ | --------- | ------------ | -----: |
| El problema | Integrante 1 | 1 – 4 | 2:55 |
| Los datos | Integrante 2 | 5 – 8 | 3:45 |
| Patrones temporales | Integrante 3 | 9 – 12 | 4:15 |
| Relaciones y cierre | Integrante 4 | 13 – 16 | 3:50 |
| | | **Total** | **14:45** |

| # | Diapositiva | Figura | Tiempo |
| -: | ----------- | ------ | -----: |
| 1 | Portada | — | 0:15 |
| 2 | ¿Qué es el almacenamiento total de agua? | `18_mapa_promedio` | 1:00 |
| 3 | El problema: la información llega tarde | — | 0:50 |
| 4 | Problema científico y objetivos | — | 0:50 |
| 5 | Descripción del dataset | — | 0:45 |
| 6 | Calidad: lo que el conteo de nulos no ve | `10_cobertura_temporal` | 1:20 |
| 7 | Distribuciones de las variables | `14_histogramas_variables` | 0:40 |
| 8 | Valores atípicos: por qué no los eliminamos | `15_atipicos_tiempo_espacio` | 1:00 |
| 9 | Patrones temporales: una tendencia descendente | `16_media_movil` | 1:05 |
| 10 | Descomposición: ¿dónde está la variabilidad? | `17_descomposicion` | 1:00 |
| 11 | La estacionalidad que casi no vemos | `17_perfil_estacional` | 1:20 |
| 12 | Cada región se comporta distinto | `18_series_por_banda` | 0:50 |
| 13 | Principales relaciones entre variables | `19_matriz_correlacion` | 1:05 |
| 14 | La línea base que hay que superar | `19_linea_base_persistencia` | 0:55 |
| 15 | Hallazgos más importantes | — | 0:50 |
| 16 | Conclusiones y próximos pasos | — | 1:00 |

## Recomendaciones para ensayar

- **Cronometrar por bloque, no por diapositiva.** Si un bloque se pasa de su
  tiempo, el siguiente expositor lo paga. Las tres diapositivas con más margen para
  recortar son la 5, la 7 y la 15: son de repaso y se pueden acelerar sin perder
  el hilo.
- **No leer las viñetas.** La audiencia las lee más rápido de lo que se pueden
  decir. Las notas del orador están escritas como indicaciones de qué contar y qué
  señalar en la figura, no como texto para recitar.
- **Las tres diapositivas que no conviene apurar** son la 6 (los faltantes que el
  conteo de nulos no detecta), la 11 (la estacionalidad que se cancela entre
  hemisferios) y la 14 (la línea base). Son los aportes propios del análisis.
- **Preparar las transiciones.** Al final de las diapositivas 4, 8 y 12 hay un
  cambio de expositor; conviene cerrar con una frase que enlace con lo siguiente.

## Preguntas probables y cómo responderlas

**¿Por qué no eliminaron los valores atípicos?**
Porque se agrupan en años y regiones concretos, que es la firma de eventos
hidrológicos reales y no de errores de medición, y porque son justamente las
sequías que el reto busca anticipar. La figura de la diapositiva 8 lo muestra.

**¿Por qué la estacionalidad sale tan baja si el agua tiene ciclo anual?**
Porque los hemisferios tienen ciclos opuestos y se cancelan al promediarse, y
porque el 80.3 % de las celdas están en el norte. Al separar por banda de latitud
el ciclo reaparece.

**¿Se puede decir cuánta agua se perdió?**
No. Las variables vienen estandarizadas y son adimensionales, no están en
centímetros de lámina de agua. Solo se pueden interpretar como desviaciones
relativas.

**¿El SPEI causa el cambio en el almacenamiento?**
No se puede afirmar. Lo que se observa es una asociación; ambas variables pueden
responder a un mismo balance hídrico de fondo.

**¿Por qué no entrenaron un modelo?**
Porque esta etapa del proyecto es exploratoria. Además, el análisis reveló
condiciones —los meses faltantes y el enmascaramiento del conjunto de prueba— que
habrían invalidado un modelo construido antes de entenderlas.

**¿Qué tan buena es la línea base de persistencia?**
RMSE 0.5724, equivalente al 62.8 % de la desviación estándar de la variable
objetivo. Es exigente: cualquier modelo tiene que bajar de ahí para aportar algo.
