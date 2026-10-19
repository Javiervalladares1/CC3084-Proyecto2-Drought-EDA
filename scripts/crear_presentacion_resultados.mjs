// Ejecutar una copia en tmp/presentacion_build con node_modules enlazado al runtime.
import fs from "node:fs/promises";
import path from "node:path";
import {pathToFileURL} from "node:url";
import {Presentation, PresentationFile} from "@oai/artifact-tool";

const root = path.resolve(process.argv[2] ?? process.cwd());
const skill = "/Users/javiervalladares/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations";
const python = "/Users/javiervalladares/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const buildDir = path.join(root,"tmp/presentacion_build");
const output = path.join(root,"output/presentacion/Proyecto2_Resultados_TWS_Final.pptx");
const {finalizePresentation, applyPresentationChartFont} = await import(pathToFileURL(path.join(skill,"container_tools/artifact_tool_utils.mjs")).href);
const read = async file => JSON.parse(await fs.readFile(file,"utf8"));
const results = path.join(root,"outputs/modelado");
const summary = await read(path.join(results,"resumen_resultados.json"));
const audit = await read(path.join(results,"auditoria.json"));
const cfg = await read(path.join(root,"config/modelado.json"));
const families = ["random_forest","xgboost","lstm"];
const labels = {random_forest:"Random Forest",xgboost:"XGBoost",lstm:"LSTM"};
const shades = ["#151515","#666666","#AAAAAA"];
const held = Object.fromEntries(summary.holdout_results.map(r=>[r.family,r]));
const selected = {};
const confirmation = {};
for (const family of families) {
  selected[family] = await read(path.join(results,`seleccion_${family}.json`));
  confirmation[family] = await read(path.join(root,`models/confirmation/${family}/complete.json`));
}
const presentation = Presentation.create({slideSize:{width:1280,height:720}});
const font = "Arial";
const chartSlides = [];
const tableSlides = [];
const script = [];
const format = (v,n=4) => Number(v).toFixed(n);
const count = v => Number(v).toLocaleString("es-GT");
function text(slide,value,left,top,width,height,size=28,bold=false) {
  const shape = slide.shapes.add({geometry:"textbox",position:{left,top,width,height},fill:"none",line:{fill:"none",width:0}});
  shape.text=value;
  shape.text.style={fontSize:size,typeface:font,color:"#000000",bold,wrap:"square",verticalAlignment:"top",insets:0,autoFit:"none"};
  return shape;
}
function slide(title,notes,seconds=55) {
  const s=presentation.slides.add();
  s.background.fill="#FFFFFF";
  text(s,title,72,45,1136,100,44,true);
  const index=presentation.slides.items.length;
  s.speakerNotes.text=`Tiempo sugerido ${seconds} segundos\n\n${notes}\n\nFuentes de resultados: outputs/modelado/resumen_resultados.json y manifiestos de modelos. Datos: Zindi/ITU, https://zindi.world/competitions/one-step-ahead-of-drought-forecasting-global-water-storage-challenge`;
  script.push({slide:index,title,seconds,notes});
  return s;
}
function body(s,paragraphs,{left=72,top=170,width=1136,size=29,gap=108}={}) {
  paragraphs.forEach((p,i)=>text(s,p,left,top+i*gap,width,gap-18,size));
}
function chart(s,type,categories,series,opts={}) {
  const position=opts.position??{left:72,top:165,width:1136,height:420};
  // Excel conserva los valores de las gráficas a seis decimales; las métricas
  // completas permanecen en los CSV y la presentación muestra cuatro decimales.
  series = series.map(r=>({...r,values:r.values.map(v=>v===null?null:Number(Number(v).toFixed(6)))}));
  const ch=s.charts.add(type,{position,categories,series,
    hasLegend:series.length>1,legend:{position:"bottom",textStyle:{fontSize:22,fill:"#000000"}},
    chartFill:"#FFFFFF",chartLine:{fill:"none",width:0},plotAreaFill:"#FFFFFF",plotAreaLine:{fill:"none",width:0},
    barOptions:{direction:"column",grouping:"clustered",gapWidth:100},
    lineOptions:{smooth:false},
    xAxis:{textStyle:{fontSize:22,fill:"#000000"},line:{fill:"#000000",width:1},majorGridlines:null},
    yAxis:{min:opts.min??0,numberFormatCode:opts.format??"0.000",title:{text:opts.ytitle??"RMSE",textStyle:{fontSize:22,fill:"#000000"}},
           textStyle:{fontSize:22,fill:"#000000"},majorGridlines:{fill:"#DDDDDD",width:1}},
    dataLabels:{showValue:opts.showValue??type==="bar",position:"outEnd",numberFormatCode:opts.format??"0.0000",textStyle:{fontSize:23,fill:"#000000"}}
  });
  applyPresentationChartFont(ch,{fontFamily:font});
  chartSlides.push(presentation.slides.items.length);
  return ch;
}
function table(s,values,widths,{top=165,height=370}={}) {
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:72,top,width:1136,height,columnWidths:widths,values});
  t.borders.assign({fill:"#333333",style:"solid",width:.7});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:"#FFFFFF",textStyle:{typeface:font,fontSize:24,color:"#000000"},margins:{left:12,right:12,top:10,bottom:10},anchor:"middle"});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({textStyle:{bold:true,typeface:font,fontSize:24,color:"#000000"}});
  tableSlides.push(presentation.slides.items.length);
  return t;
}
function note(s,value) {text(s,value,72,615,1136,80,23);}

let s=slide("Pronóstico del almacenamiento total de agua", "Presentar el problema, las tres familias y el propósito de comparar resultados fuera de muestra.",30);
text(s,"Resultados del Proyecto 2",72,198,1136,70,42);
text(s,"Random Forest, XGBoost y LSTM",72,292,1136,55,32);
text(s,"Javier Valladares 23045\nIan Cumes 23236\nJavier Cifuentes 23079",72,400,1000,140,27);
text(s,"CC3084 Data Science   Universidad del Valle de Guatemala\nSemestre II de 2026   13 de octubre de 2026",72,592,1136,70,23);

s=slide("El problema y la información disponible", "Explicar que el objetivo es continuo, que t+1 es calendario y que el horizonte desde el último TWS cambia con sus faltantes. No interpretar valores estandarizados como centímetros. Fuente oficial del reto.",55);
body(s,["Pronosticar el TWS del siguiente mes calendario con información conocida hasta la emisión.",
        "TWS integra reservas superficiales y subterráneas. Los productos GRACE llegan con retraso.",
        "El 66.5 % del TWS actual está oculto en Test. El horizonte efectivo desde la última observación puede llegar a siete meses.",
        "La tarea es regresión y se evalúa mediante RMSE en la escala estandarizada del reto."],{gap:108,size:29});

s=slide("Datos y hallazgos exploratorios", "Destacar cantidad de filas frente a cantidad de meses independientes. Explicar el calendario y el desbalance espacial. Las cantidades proceden de la auditoría local.",55);
table(s,[["Característica","Entrenamiento","Test"],["Observaciones",count(audit.train_rows),count(audit.test_rows)],
         ["Meses observados",String(audit.train_observed_months),String(audit.test_observed_months)],
         ["Periodo de entrada","2002-05 a 2015-08","2015-09 a 2018-12"],["Etiquetas","Disponibles","No disponibles"]],[400,368,368],{height:350});
note(s,`${count(audit.cells)} celdas de 1°. Faltan 22 meses del calendario de Train y el ${(audit.north_fraction*100).toFixed(1)} % de las filas pertenece al hemisferio norte.`);

s=slide("Comparación temporal antes de la prueba final", "Describir selección de configuraciones y de familia. La última etiqueta de entrenamiento precede a la primera de evaluación. La fecha usada es el mes del objetivo. No dividir filas aleatoriamente.",70);
table(s,[["Etapa","Entrenamiento","Evaluación","Filas"],
         ["Ajuste","Hasta 2010-12","2011-2012 presentes",count(audit.partitions.ajuste_validacion.rows)],
         ["Confirmación","Hasta 2012-10","2013 presentes",count(audit.partitions.confirmacion_validacion.rows)],
         ["Prueba final","Hasta 2013-12","2014-2015 presentes",count(summary.holdout_rows)]],[280,280,330,246],{height:350});
note(s,"La selección se fijó en 2013. La prueba final nunca se utilizó para ajustar parámetros o detener el entrenamiento.");

s=slide("Literatura y elección de las tres familias", "Citar los antecedentes aplicados y distinguir reconstrucción de pronóstico. Random Forest y boosting aparecen en A. Y. Sun et al. 2021. Li y Kusche 2026 y Palazzoli et al. 2025 respaldan memoria temporal. DOI: 10.1029/2020WR028666; 10.1029/2025WR041710; 10.1038/s41597-025-04403-3.",55);
table(s,[["Familia","Razón de inclusión","Antecedente"],
         ["Random Forest","Interacciones no lineales y referencia tabular","Breiman 2001 y A. Y. Sun et al. 2021"],
         ["XGBoost","Árboles secuenciales y regularización","A. Y. Sun et al. 2021"],
         ["LSTM","Memoria hidrológica en secuencias","Palazzoli et al. 2025 y Li y Kusche 2026"]],[250,470,416],{height:350});
note(s,"Nueve antecedentes y dos fundamentos científicos. El informe incluye referencias APA y evidencia de indexación.");

s=slide("Entradas causales compartidas", "Explicar que los árboles reciben 57 valores aplanados y la LSTM la misma información organizada como secuencia y contexto. No usar target(t-1) para recuperar TWS oculto. El cero de relleno tiene indicadores explícitos.",60);
body(s,["Seis meses calendario con ocho canales por paso: clima, TWS observable e indicadores de disponibilidad.",
        "Nueve variables de contexto: estacionalidad, última observación y antigüedad, ubicación y tiempo transcurrido.",
        "Las tres familias predicen una corrección respecto del último TWS permitido. No se usa información futura.",
        `Máscara sintética de ${(audit.synthetic_mask_rate*100).toFixed(2)} %, aplicada por bloques temporales compartidos entre celdas.`],{gap:108,size:28});

for (const family of families.slice(0,2)) {
  const sel=selected[family];
  const records=[];
  for (const params of cfg[family]) records.push(await read(path.join(root,`models/tuning/${family}/${params.name}/complete.json`)));
  s=slide(`${labels[family]} y ajuste de configuraciones`, `Explicar tres configuraciones y elegir por RMSE de validación. La configuración seleccionada es ${sel.configuration.name}. Los tiempos completos están en el informe. La mayor complejidad no garantiza mejor validación.`,55);
  chart(s,"bar",records.map(r=>r.name),[{name:"RMSE de validación",values:records.map(r=>r.validation.rmse),fill:"#666666",points:records.map((r,i)=>({idx:i,fill:r.name===sel.configuration.name?"#111111":"#AAAAAA"}))}],{ytitle:"RMSE de validación 2011-2012"});
  note(s,family==="random_forest"?`${sel.configuration.name}: ${sel.configuration.n_estimators} árboles, profundidad ${sel.configuration.max_depth}, mínimo ${sel.configuration.min_samples_leaf} por hoja.`:
       `${sel.configuration.name}: profundidad ${sel.configuration.max_depth}, tasa ${sel.configuration.learning_rate} y ${sel.tuning.best_iterations} iteraciones.`);
}

s=slide("LSTM y parada temprana", "Describir una capa recurrente y una cabeza densa. Las tres configuraciones mejoraron inicialmente y luego sobreajustaron validación temporal. Se recuperó la mejor época, no la última. La red seleccionada usa el número de épocas fijado en validación.",60);
const learning=[];
for (const params of cfg.lstm) learning.push(await read(path.join(root,`models/tuning/lstm/${params.name}/metadata.json`)));
const maxEpoch=Math.min(...learning.map(r=>r.learning_history.length));
chart(s,"line",Array.from({length:maxEpoch},(_,i)=>String(i+1)),learning.map((r,i)=>({name:cfg.lstm[i].name,values:Array.from({length:maxEpoch},(_,j)=>r.learning_history[j]?.validation_rmse??null),line:{fill:shades[i],width:3},marker:{symbol:["circle","square","triangle"][i],size:6,fill:shades[i]}})),{min:.5,ytitle:"RMSE de validación",showValue:false});
note(s,`${selected.lstm.configuration.name}: ${selected.lstm.configuration.hidden_size} unidades LSTM, ${selected.lstm.configuration.head_size} densas, dropout ${selected.lstm.configuration.dropout} y ${selected.lstm.tuning.best_epochs} época seleccionada.`);

s=slide("Resultados de la prueba temporal reservada", "Comparar siempre con referencias bajo la misma máscara y fechas. Estos resultados pertenecen a 265447 filas de 17 meses observados de 2014-2015. El archivo Test no tiene etiquetas y no aparece como una evaluación de precisión.",65);
const comparisons=[...families.map(f=>({name:labels[f],rmse:held[f].rmse})),...summary.baselines_holdout.map(r=>({name:r.algorithm==="Persistencia causal"?"Persistencia":"Climatología",rmse:r.rmse}))];
chart(s,"bar",comparisons.map(r=>r.name),[{name:"RMSE",values:comparisons.map(r=>r.rmse),fill:"#777777",points:comparisons.map((r,i)=>({idx:i,fill:[...shades,"#CCCCCC","#EEEEEE"][i]}))}],{ytitle:"RMSE fuera de muestra"});
note(s,`Mejora frente a persistencia: RF ${format(held.random_forest.improvement_vs_persistence_pct,1)} %, XGBoost ${format(held.xgboost.improvement_vs_persistence_pct,1)} % y LSTM ${format(held.lstm.improvement_vs_persistence_pct,1)} %.`);

s=slide("Disponibilidad de TWS y precisión", "Mostrar que disponer del TWS actual cambia las condiciones de predicción. Los grupos tienen fechas diferentes, por lo que no se interpreta como efecto causal aislado. La tabla completa de antigüedad y región está en la entrega.",55);
chart(s,"bar",["Observado","Oculto"],families.map((f,i)=>({name:labels[f],values:["Observado","Oculto"].map(a=>summary.by_availability.find(r=>r.family===f&&r.availability===a).rmse),fill:shades[i]})),{ytitle:"RMSE por disponibilidad",showValue:false});
note(s,"Se conservan la última observación conocida, su antigüedad y los indicadores de faltantes. La historia nunca se reconstruye con etiquetas ocultas.");

s=slide("El error cambia entre regiones", "Relacionar el desbalance espacial y el error por región. No interpretar el promedio global como una garantía para todas las celdas. La evaluación usa ubicaciones conocidas y nuevas fechas.",55);
const regions=[...new Set(summary.by_region.map(r=>r.region))];
chart(s,"bar",regions.map(r=>r.replace("extratropical","extratrop.")),families.map((f,i)=>({name:labels[f],values:regions.map(region=>summary.by_region.find(r=>r.family===f&&r.region===region).rmse),fill:shades[i]})),{ytitle:"RMSE regional",showValue:false});
note(s,"La evaluación regional complementa el RMSE agrupado del reto. La transferencia a regiones completamente nuevas requiere otra validación.");

s=slide("Eficiencia e incertidumbre de la comparación", "Explicar tiempos locales con modelos cargados. La LSTM tiene el menor RMSE final descriptivo, pero la diferencia frente a XGBoost incluye cero en el intervalo de bloques temporales. La selección previa fue XGBoost. No atribuir superioridad universal al ganador de una sola prueba.",70);
table(s,[["Algoritmo","RMSE","Ajuste s","ms / 1 000 filas"],...families.map(f=>[labels[f],format(held[f].rmse),format(held[f].fit_seconds,1),format(held[f].inference_ms_per_1000,2)])],[350,230,260,296],{height:310});
const pair=summary.uncertainty.paired_differences.find(r=>r.first==="xgboost"&&r.second==="lstm");
note(s,`Diferencia XGBoost menos LSTM: ${format(pair.difference_rmse)}. Intervalo por bloques [${format(pair.ci_low)}, ${format(pair.ci_high)}], que incluye cero.`);

s=slide("Aplicación para explorar y pronosticar", "Demostrar la aplicación. La captura muestra una predicción real con modelos de producción. Se puede cargar CSV y elegir uno o los tres modelos. Las métricas provienen de modelos separados que conservaron la prueba reservada.",65);
const appScreenshotBytes=await fs.readFile(path.join(root,"figures/resultados/app_pronosticar.jpg"));
s.images.add({blob:appScreenshotBytes,contentType:"image/jpeg",alt:"Aplicación con una predicción real de los tres modelos",fit:"contain",position:{left:72,top:155,width:1136,height:440}});
note(s,"Formulario o CSV, preparación automática, comparación de modelos y descarga de predicciones. El rendimiento interactivo puede mostrarse u ocultarse.");

s=slide("Conclusiones y límites de uso", "Concluir sobre cumplimiento de objetivos y condiciones de validez. El resultado no es una categoría de sequía ni volumen físico. Test no tiene etiquetas y las fechas futuras pueden cambiar de distribución. Las 280961 predicciones por algoritmo están completas.",60);
body(s,[`${labels[summary.recommended_family]} quedó seleccionado con 2013. LSTM obtuvo el menor RMSE final descriptivo, con una diferencia pequeña e incierta frente a XGBoost.`,
        "Las tres familias mejoraron la persistencia causal. La evaluación regional y por faltantes ayuda a interpretar esa mejora.",
        "La aplicación comparte el preprocesamiento del entrenamiento y distingue prueba reservada de producción.",
        "La evidencia corresponde a fechas futuras en celdas conocidas. No hay etiquetas de Test para verificar precisión en 2015-2018."],{gap:108,size:28});

s=slide("Entrega y reproducción del proyecto", "Indicar dónde están los entregables y el comando de la aplicación. El informe incluye once referencias científicas y bibliografía técnica, y explica el protocolo y los resultados. Aclarar que los datos originales se descargan desde Zindi para reentrenar.",35);
body(s,["Informe final en Word y PDF, con referencias APA, metodología, resultados y capturas.",
        "Código y notebook ejecutado, modelos guardados, tablas, figuras y predicciones completas de Test.",
        "Aplicación local: python -m streamlit run app.py",
        "Repositorio: github.com/Javiervalladares1/CC3084-Proyecto2-Drought-EDA"],{gap:105,size:28});

await fs.mkdir(buildDir,{recursive:true});
await fs.mkdir(path.dirname(output),{recursive:true});
await fs.mkdir(path.join(buildDir,"slides"),{recursive:true});
for (const [index,slide] of presentation.slides.items.entries()) {
  const png=await presentation.export({slide,format:"png",scale:1});
  await fs.writeFile(path.join(buildDir,"slides",`slide-${String(index+1).padStart(2,"0")}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(buildDir,"candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidate);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:output,pythonExecutable:python,
  integrityValidatorPath:path.join(skill,"container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath:path.join(skill,"container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs:["--expected-slide-size-emu","12192000,6858000","--validate-bullet-geometry","--validate-heading-fit",...tableSlides.flatMap(n=>["--require-native-table-slide",String(n)])],
  explicitTotalSlideCount:presentation.slides.items.length,
  requiredNativeTableOwnerSlides:tableSlides,requiredNativeChartOwnerSlides:[...new Set(chartSlides)],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:"design",families:[font]},verifyArtifactToolImport:true,
  receiptPath:path.join(buildDir,"validation_final.json")});
await fs.writeFile(path.join(root,"docs/Guion_Presentacion_Resultados.json"),JSON.stringify(script,null,2));
console.log(JSON.stringify({output,slides:presentation.slides.items.length,seconds:script.reduce((sum,r)=>sum+r.seconds,0)}));
