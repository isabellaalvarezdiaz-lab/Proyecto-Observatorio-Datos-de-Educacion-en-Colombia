# Tablero: Nada sin fuente — Observatorio de Datos de Educación en Colombia
# install.packages(c("shiny", "bslib", "plotly"))
# Ejecutar: shiny::runApp("tablero_nada_sin_fuente")

library(shiny)
library(bslib)
library(plotly)

# ---- Paleta -----------------------------------------------------------
tinta <- "#0A1A3F"; mar <- "#2F6DB5"; ambar <- "#C8A24B"; coral <- "#A94438"
niebla <- "#E6ECF5"; gris <- "#5B6677"

tema <- bs_theme(
  version = 5, bg = "#F6F8FB", fg = tinta, primary = mar,
  base_font = font_google("Instrument Sans"),
  heading_font = font_google("Newsreader")
)

css <- sprintf("
body{background:radial-gradient(1000px 520px at 95%% -10%%,rgba(14,124,134,.16),transparent 60%%),radial-gradient(900px 520px at -10%% 8%%,rgba(200,162,75,.12),transparent 60%%),#F3F6FA}
.navbar{background:linear-gradient(90deg,%1$s,#12306A)!important;box-shadow:0 8px 24px rgba(20,33,61,.28)}
.navbar .navbar-brand{color:#fff!important;font-family:'Newsreader',serif;font-size:1.4rem;display:flex;align-items:center;gap:.7rem}
.navbar .navbar-brand img{background:#fff;border-radius:8px;padding:3px 6px}
.navbar .nav-link{color:#C9D4E5!important;transition:color .2s}
.navbar .nav-link:hover{color:#fff!important}
.navbar .nav-link.active{color:%3$s!important;border-bottom-color:%3$s!important}
.hero{position:relative;overflow:hidden;display:flex;gap:2rem;align-items:center;justify-content:space-between;
  background:linear-gradient(135deg,%1$s 0%%,#12306A 58%%,%4$s 135%%);color:#fff;border-radius:24px;
  padding:2.8rem;margin-bottom:1.6rem;box-shadow:0 22px 48px rgba(20,33,61,.3);animation:subir .8s ease-out both}
.hero::before{content:'';position:absolute;right:-90px;top:-110px;width:340px;height:340px;border-radius:50%%;background:rgba(200,162,75,.22)}
.hero::after{content:'';position:absolute;left:30%%;bottom:-150px;width:300px;height:300px;border-radius:50%%;background:rgba(47,109,181,.30)}
.hero>*{position:relative;z-index:1}
.hero h1{font-size:3.2rem;margin:0 0 .3rem}
.hero .pregunta{font-family:'Newsreader',serif;font-style:italic;font-size:1.7rem;color:%3$s;margin:1.2rem 0 .3rem}
.hero small{color:#C9D4E5}
.hero-logo{background:#fff;color:%1$s;border-radius:18px;padding:1rem 1.4rem;text-align:center;box-shadow:0 12px 28px rgba(0,0,0,.25);min-width:170px}
.hero-logo img{max-height:100px;max-width:200px}
@keyframes subir{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
h2{font-weight:700;margin-top:.4rem}
h2::after{content:'';display:block;width:70px;height:5px;border-radius:5px;margin-top:.45rem;background:linear-gradient(90deg,%3$s,%4$s)}
.fuente{display:inline-flex;gap:.5rem;align-items:center;background:#fff;color:%4$s;border:1px solid %4$s;
  border-radius:999px;padding:.25rem .9rem;font-size:.85rem;margin:.6rem 0 1rem;box-shadow:0 3px 10px rgba(14,124,134,.12)}
.tarjeta{position:relative;background:#fff;border-radius:18px;padding:1.3rem 1.5rem;border:1px solid #E1E7EF;border-top:5px solid %3$s;
  height:100%%;box-shadow:0 10px 26px rgba(20,33,61,.09);transition:transform .2s,box-shadow .2s}
.tarjeta:hover{transform:translateY(-4px);box-shadow:0 18px 36px rgba(20,33,61,.16)}
.tarjeta h5{font-family:'Newsreader',serif;font-size:1.3rem}
.cifra{font-family:'Newsreader',serif;font-size:2.6rem;line-height:1;font-weight:700}
.cifra-icono{position:absolute;right:1.1rem;top:1rem;font-size:1.8rem;opacity:.22}
.tbl{width:100%%;border-collapse:collapse;font-size:.95rem}
.tbl th{text-align:left;border-bottom:3px solid %3$s;padding:.55rem .6rem}
.tbl td{border-bottom:1px solid #E3E8EF;padding:.55rem .6rem;vertical-align:top}
.tbl tbody tr:hover{background:%2$s}
.antes{color:%5$s;text-decoration:line-through}.despues{color:%4$s;font-weight:600}
.paso{background:#fff;border-left:6px solid %4$s;border-radius:10px;padding:.75rem 1rem;margin-bottom:.6rem;box-shadow:0 4px 12px rgba(20,33,61,.07)}
.paso.mal{border-color:%5$s;background:#FFF5F4}.paso.ok{border-color:%4$s;background:#F0FAFA}
.accordion{--bs-accordion-border-radius:14px;box-shadow:0 8px 22px rgba(20,33,61,.08);border-radius:14px;overflow:hidden}
.btn-primary{box-shadow:0 6px 14px rgba(47,109,181,.30)}
.cierre{font-family:'Newsreader',serif;font-size:2.4rem;line-height:1.3;max-width:900px;padding-left:1.4rem;border-left:8px solid %3$s}
", tinta, niebla, ambar, mar, coral)

secc <- data.frame(
  t = c("1 · Diagnóstico","2 · Experimento","3 · Decisión","4 · Sistema","5 · Evaluación","6 · Correcciones","7 · Uso de IA","8 · Cierre"),
  ico = c("magnifying-glass","flask","scale-balanced","gears","chart-column","pen-to-square","robot","flag-checkered"),
  d = c("Qué nos inventó la IA","Cuánto inventa cada herramienta","Por qué NotebookLM","Del corpus a la trazabilidad",
        "22 preguntas: sistema vs control","7 afirmaciones corregidas","Qué se delegó y qué no","Lo que sale de los datos")
)
css <- paste0(css, "
body{background:radial-gradient(900px 500px at 100% 0,rgba(47,109,181,.16),transparent 60%),radial-gradient(800px 500px at 0 20%,rgba(200,162,75,.12),transparent 60%),radial-gradient(700px 500px at 60% 100%,rgba(10,26,63,.07),transparent 60%),#F1F4F9}
.hero{background:linear-gradient(120deg,#0A1A3F,#1F3F8F 50%,#2F6DB5,#0A1A3F);background-size:300% 300%;animation:subir .8s ease-out both,flujo 14s ease infinite}
@keyframes flujo{0%{background-position:0 50%}50%{background-position:100% 50%}100%{background-position:0 50%}}
.hero::before{animation:flota 7s ease-in-out infinite}.hero::after{animation:flota 9s ease-in-out infinite reverse}
@keyframes flota{50%{transform:translateY(22px) scale(1.06)}}
.hero-logo .shiny-input-container{margin:.6rem 0 0}.hero-logo .btn{font-size:.75rem;padding:.15rem .6rem}
.hero-logo .input-group{flex-wrap:nowrap}.hero-logo input[type=text]{display:none}
.container>h2{background:linear-gradient(100deg,#0A1A3F,#1F4E9C 60%,#2F6DB5);color:#fff;border-radius:16px;padding:.9rem 1.4rem;box-shadow:0 12px 28px rgba(11,31,75,.25);position:relative;overflow:hidden}
.container>h2::after{position:absolute;right:-20px;top:-30px;width:140px;height:140px;margin:0;border-radius:50%;background:rgba(200,162,75,.35)}
.tarjeta{border-top:6px solid transparent;border-image:linear-gradient(90deg,#C8A24B,#2F6DB5,#A94438) 1;border-radius:0;clip-path:inset(0 round 18px)}
.mosaico{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem;margin-top:1.4rem}
.mosaico a{text-decoration:none}
.tile{display:flex;flex-direction:column;gap:.3rem;color:#fff;border-radius:18px;padding:1.2rem 1.3rem;min-height:130px;box-shadow:0 12px 26px rgba(11,31,75,.2);transition:transform .2s}
.tile:hover{transform:translateY(-5px) rotate(-.6deg)}.tile .fa,.tile svg{font-size:1.7rem;margin-bottom:.3rem}.tile span{opacity:.9;font-size:.9rem}
.mosaico a:nth-child(1) .tile{background:linear-gradient(135deg,#C0594C,#A94438)}.mosaico a:nth-child(2) .tile{background:linear-gradient(135deg,#2F6DB5,#4F86C6)}
.mosaico a:nth-child(3) .tile{background:linear-gradient(135deg,#3E6FB0,#4A57A6)}.mosaico a:nth-child(4) .tile{background:linear-gradient(135deg,#C8A24B,#A9842F)}
.mosaico a:nth-child(5) .tile{background:linear-gradient(135deg,#2D3A7C,#4B5BA8)}.mosaico a:nth-child(6) .tile{background:linear-gradient(135deg,#1F7A8C,#14506B)}
.mosaico a:nth-child(7) .tile{background:linear-gradient(135deg,#1B2F66,#3A4F8E)}.mosaico a:nth-child(8) .tile{background:linear-gradient(135deg,#0A1A3F,#3E6FB0)}
.pipeline{display:flex;flex-direction:column;gap:.4rem}
.pipeline span{display:block;color:#fff;font-weight:600;border-radius:12px;padding:.8rem 1rem;position:relative}
.pipeline span svg{margin-right:.6rem}
.pipeline span:nth-child(1){background:linear-gradient(90deg,#3E6FB0,#4A57A6)}.pipeline span:nth-child(2){background:linear-gradient(90deg,#2F6DB5,#4F86C6)}
.pipeline span:nth-child(3){background:linear-gradient(90deg,#C8A24B,#A9842F)}.pipeline span:nth-child(4){background:linear-gradient(90deg,#1B2F66,#3A4F8E)}
.pipeline span:not(:last-child)::after{content:'\\25BC';position:absolute;left:1.2rem;bottom:-1.05rem;color:#0A1A3F;font-size:.8rem;z-index:2}
.pipeline{padding-bottom:.4rem}
.pie{margin-top:3rem;padding:1.6rem 2rem;display:flex;gap:1.4rem;align-items:center;justify-content:center;color:#fff;text-align:left;
  background:linear-gradient(90deg,#0A1A3F,#1F3F8F,#2F6DB5)}
.pie img{background:#fff;border-radius:10px;padding:5px 9px;height:54px}
")

css <- paste0(css, "
.apilado{display:flex;flex-direction:column;gap:1rem;height:100%}.apilado>.tarjeta,.apilado>div{height:auto;margin:0!important}
.tarjeta{border:1px solid #D9E1EE;border-top:5px solid #1F4E9C;border-image:none;clip-path:none;border-radius:18px;box-shadow:0 8px 22px rgba(10,26,63,.10)}
.hero{box-shadow:0 16px 36px rgba(10,26,63,.30)}
")

css <- paste0(css, "
.hero-logo{background:transparent;color:#fff;padding:0;box-shadow:none;min-width:0;text-align:center}
.hero-logo img{max-height:140px;max-width:220px;border-radius:18px;border:2px solid rgba(255,255,255,.35);box-shadow:0 16px 34px rgba(0,0,0,.4)}
.hero-logo .progress{display:none}
.hero-logo .btn-file{background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.45)}
.navbar .navbar-brand img{background:transparent;padding:0;border-radius:7px}
.pie img{background:transparent;padding:0;border-radius:10px;height:62px}
")

fuente <- function(...) div(class = "fuente", icon("file-lines"), span("Fuente: ", ...))
tabla <- function(df) {
  tags$table(class = "tbl",
             tags$thead(tags$tr(lapply(names(df), tags$th))),
             tags$tbody(apply(df, 1, function(r) tags$tr(lapply(r, function(x) tags$td(HTML(x))))))
  )
}
tarjeta <- function(...) div(class = "tarjeta", ...)
cifra <- function(n, txt, col = tinta, ico = "circle-check") tarjeta(span(class = "cifra-icono", icon(ico)), div(class = "cifra", style = paste0("color:", col), n), p(txt, style = paste0("color:", gris, ";margin:.4rem 0 0")))

# ---- Datos ------------------------------------------------------------
exp_df <- data.frame(
  trat = c("A · Chat sin documentos", "B · Consensus", "C · NotebookLM"),
  util = c(9, 11, 14), p = c(60.0, 73.3, 93.3), lo = c(35.7, 48.0, 70.2), hi = c(80.2, 89.1, 98.8),
  existe = c(3, 4, 0), noexiste = c(3, 0, 1),
  lab = c("9 de 15 = 60,0 %", "11 de 15 = 73,3 %", "14 de 15 = 93,3 %")
)
secc <- data.frame(
  t = c("1 · Lo que inventó la IA", "2 · Experimento", "3 · Decisión", "4 · Sistema", "5 · Evaluación", "6 · Límites"),
  ico = c("magnifying-glass", "flask", "scale-balanced", "gears", "chart-column", "flag-checkered"),
  d = c("Lo que nos inventó la IA", "El experimento: cuánto inventa cada herramienta", "La decisión",
        "El sistema", "La evaluación", "Límites y lo que no delegamos")
)
fte <- function(...) p(class = "fte", "Fuente: ", ...)
css <- paste0(css, "
.fte{font-size:.78rem;color:#5B6677;border-top:1px solid #D9E1EE;margin-top:1.8rem;padding-top:.7rem}
.linea{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center}
.linea span{background:#fff;border:1px solid #D9E1EE;border-radius:10px;padding:.6rem .9rem;font-weight:600;box-shadow:0 4px 12px rgba(10,26,63,.08)}
.linea span:not(:last-child)::after{content:'\\2192';margin-left:.7rem;color:#1F4E9C}
.linea.plano span::after{content:none!important}
.menudo{font-size:.85rem;color:#5B6677}
.destacado{background:linear-gradient(120deg,#0A1A3F,#1F4E9C);color:#fff;border-radius:18px;padding:1.3rem 1.6rem;font-family:'Newsreader',serif;font-size:1.35rem;box-shadow:0 12px 28px rgba(10,26,63,.25)}
")
css <- paste0(css, "
.tab-pane.active .tarjeta,.tab-pane.active .paso,.tab-pane.active .linea span{animation:subir .6s ease-out backwards}
.tab-pane.active .destacado{animation:subir .8s .2s ease-out backwards}
.pager{display:flex;justify-content:space-between;margin-top:2rem}
.pager a{background:#0A1A3F;color:#fff;padding:.55rem 1.2rem;border-radius:999px;text-decoration:none;font-weight:600;box-shadow:0 6px 14px rgba(10,26,63,.25);transition:transform .2s,background .2s}
.pager a:hover{background:#1F4E9C;transform:translateY(-2px)}.pager a:only-child{margin-left:auto}
.tab-pane.active .cifra{animation:subir .7s ease-out backwards}
")
js <- "
function contar(el){var o=el.getAttribute('data-o')||el.textContent;el.setAttribute('data-o',o);var t0=null;
  function paso(ts){if(!t0)t0=ts;var k=Math.min((ts-t0)/1000,1);k=1-Math.pow(1-k,3);
    el.textContent=o.replace(/\\d+/g,function(n){return Math.round(parseInt(n)*k)});if(k<1)requestAnimationFrame(paso);}
  requestAnimationFrame(paso);}
function todos(){document.querySelectorAll('.tab-pane.active .cifra').forEach(contar)}
document.addEventListener('shown.bs.tab',function(){window.scrollTo({top:0,behavior:'smooth'});setTimeout(todos,60)});
"
pan <- function(i, ...) nav_panel(secc$t[i], icon = icon(secc$ico[i]), div(class = "container py-3", ...,
                                                                           div(class = "pager", if (i > 1) actionLink(paste0("ant", i), "\u2190 Anterior"),
                                                                               if (i < nrow(secc)) actionLink(paste0("sig", i), "Siguiente \u2192"))))

# ---- Interfaz ---------------------------------------------------------
ui <- page_navbar(
  title = tagList(uiOutput("logo_nav", inline = TRUE), "Nada sin fuente"), theme = tema, id = "nav",
  fillable = FALSE, underline = TRUE, header = tags$head(tags$style(HTML(css)), tags$script(HTML(js))),
  footer = div(class = "pie", uiOutput("logo_pie", inline = TRUE),
               div(strong("Universidad Santo Tomás"), br(), "Observatorio de Datos de Educación en Colombia · Nada sin fuente")),
  
  nav_panel("Inicio", icon = icon("house"), div(class = "container py-3",
                                                div(class = "hero", div(
                                                  h1("Nada sin fuente"), p("Gestión de información e IA en el proyecto"),
                                                  p(class = "pregunta", "¿De dónde sale cada afirmación?"),
                                                  tags$small("Observatorio de Datos de Educación en Colombia · Isabella Álvarez, Eduar Caicedo, Anderson González · Docente: Javier Mauricio Sierra · Universidad Santo Tomás")),
                                                  div(class = "hero-logo", uiOutput("logo_hero"), uiOutput("subir"))),
                                                div(class = "mosaico", lapply(seq_len(nrow(secc)), function(i) actionLink(paste0("ir", i),
                                                                                                                          div(class = "tile", icon(secc$ico[i]), strong(secc$t[i]), span(secc$d[i])))))
  )),
  
  pan(1, h2("Lo que nos inventó la IA"),
      p(class = "mt-3", "El proyecto mide la eficiencia del gasto de las 34 universidades públicas del país: presupuesto ejecutado frente a cobertura, graduados y desempeño en Saber Pro."),
      layout_columns(col_widths = c(4, 4, 4),
                     cifra("60 % frente a 93 %", "referencias utilizables: chat sin documentos frente a NotebookLM con nuestros artículos cargados", mar, "flask"),
                     cifra("18 de 19 frente a 2 de 19", "preguntas sobre nuestros artículos respondidas correctamente: nuestro sistema frente a un chat sin documentos", mar, "circle-check"),
                     cifra("6", "afirmaciones de nuestro anteproyecto que hubo que corregir", ambar, "pen-to-square")),
      layout_columns(col_widths = c(4, 4, 4), class = "mt-3",
                     tarjeta(h5("Caso 1 · Galvis-Aponte (2015)"),
                             p(strong("Anteproyecto: "), "62,3 % de eficiencia en cobertura"),
                             p(strong("Artículo, Cuadro 2 (p. 89): "), "63,43"),
                             p("El 62,3 está solo en el resumen, que no coincide con el cuadro."),
                             p(class = "menudo", "Páginas en la referencia: 11–40 · Páginas reales: 75–98")),
                     tarjeta(h5("Caso 2 · Melo-Becerra et al. (2017)"),
                             p(strong("La IA dijo: "), "usa DEA"), p(strong("El artículo (p. 59): "), "usa frontera estocástica"),
                             p("Un chat sin documentos repitió el mismo error.")),
                     tarjeta(h5("Caso 3 · Visbal-Cadavid et al. (2017)"),
                             p("La IA entregó una “cita textual” en español."),
                             p("El artículo está escrito en inglés: la frase no existe."))),
      div(class = "destacado mt-3", "Ninguno parecía un error. En casi todos, el artículo existía; lo falso era lo que la herramienta decía de él. No basta con comprobar que una referencia existe: hay que abrirla."),
      fte("inventarios de fallos · tabla de trazabilidad.")),
  
  pan(2, h2("El experimento: cuánto inventa cada herramienta"),
      h5(class = "mt-3", "Diseño"),
      div(class = "linea plano", span("3 integrantes × 3 herramientas × 5 referencias = 45 referencias"),
          span("reglas fijadas antes de ver las respuestas"), span("clasificación por separado y sin IA")),
      layout_columns(col_widths = c(6, 6), class = "mt-3",
                     tarjeta(h5("Las tres herramientas"),
                             p(strong("A · "), "Chat sin documentos ni internet (punto de comparación)"),
                             p(strong("B · "), "Consensus, buscador de bases académicas reales"),
                             p(strong("C · "), "NotebookLM con nuestros PDF cargados")),
                     tarjeta(h5("Definición"), p("Una referencia es utilizable si el artículo existe y dice lo que la herramienta le atribuye."))),
      layout_columns(col_widths = c(7, 5), class = "mt-3",
                     tarjeta(radioButtons("vista_exp", NULL, inline = TRUE,
                                          c("Utilizables, IC 95 % (Wilson)" = "ic", "Cómo falla cada una" = "cat")),
                             plotlyOutput("g_exp", height = 330),
                             tabla(data.frame(Herramienta = exp_df$trat, Utilizable = exp_df$util, `Existe pero no dice eso` = exp_df$existe,
                                              `No existe` = exp_df$noexiste, check.names = FALSE))),
                     div(class = "apilado",
                         tarjeta(h5("¿Qué tan seguros estamos?"),
                                 p("Diferencia NotebookLM − chat: IC 95 % de 2,6 a 58,2 puntos"), p("Prueba exacta de Fisher: p = 0,08"),
                                 p("Las referencias vienen agrupadas de a cinco por pregunta: la incertidumbre real es mayor."),
                                 p(strong("Conclusión: "), "NotebookLM supera al chat, pero no podemos decir por cuánto.")),
                         tarjeta(h5("Acuerdo entre clasificadores"), p("38 de 45 coincidencias · kappa de Fleiss = 0,72"),
                                 p("5 de los 7 desacuerdos: “existe pero no dice eso”")))),
      div(class = "destacado mt-3", "Cada herramienta resuelve un problema distinto: el buscador evita inventar artículos; el cuaderno evita tergiversar los que tiene."),
      p(class = "menudo mt-2", "La única referencia inexistente de NotebookLM apareció cuando se le pidieron cinco y no tenía cinco que dar."),
      fte("Experimento_Semana1_Final.xlsx, hojas Resultados y Consolidado.")),
  
  pan(3, h2("La decisión"),
      layout_columns(col_widths = c(6, 6), class = "mt-3",
                     tarjeta(h5("Regla en dos pasos"), p(class = "menudo", "Escrita después de las primeras pruebas; así se declara."),
                             p(strong("1. "), "Condición que no se negocia: se descarta la herramienta que no responda solo con nuestros documentos, no reconozca cuando no sabe o no diga de dónde saca lo que afirma."),
                             p(strong("2. "), "Los demás criterios se comparan sin sumarles puntos.")),
                     tarjeta(h5("El sistema propio, probado"),
                             div(class = "paso ok", strong("Búsqueda ✔ "), "encontró el Cuadro 2 de Galvis-Aponte en primer lugar"),
                             div(class = "paso ok", strong("Abstención ✔ "), "reconoció cuando no tenía la respuesta"),
                             div(class = "paso mal", strong("Redacción ✘ "), "respondió 90 % para una eficiencia de 63,43, teniendo el dato correcto delante"))),
      tarjeta(class = "mt-3", h5("Cuatro alternativas"), tabla(data.frame(
        Alternativa = c("NotebookLM", "Proyectos con archivos de los chats", "Búsqueda por programación (API)", "Sistema propio"),
        Veredicto = c("<b style='color:#2F6DB5'>ELEGIDA</b>", rep("<b style='color:#A94438'>descartada</b>", 3)),
        Motivo = c("cumple la condición y fue medida con datos propios", "citan el archivo, pero no dónde está el dato",
                   "cuesta más y no gana privacidad", "inventó una cifra con el documento en la mano")))),
      fte("hoja Tabla_Decision · anexo de pruebas de herramienta.")),
  
  pan(4, h2("El sistema"),
      layout_columns(col_widths = c(3, 3, 3, 3), class = "mt-3",
                     tarjeta(h5("13 documentos"), p("Los artículos del estado del arte")),
                     tarjeta(h5("Archivo de control"), p("De dónde salió cada documento, con qué permiso se usa y quién lo revisó")),
                     tarjeta(h5("Biblioteca en Zotero"), p("Cada referencia con su DOI o enlace")),
                     tarjeta(h5("Verificación"), p("Todos los documentos con texto legible"))),
      layout_columns(col_widths = c(6, 6), class = "mt-3",
                     tarjeta(h5("Fuera del sistema"), p("Texto completo no conseguido: Simar y Wilson (1999) y Färe et al. (1994)."), hr(),
                             h5("Instrucciones fijas de consulta"),
                             tags$ul(tags$li("Responder solo con estos documentos"), tags$li("Citar la fuente de cada oración"),
                                     tags$li("Si no está la respuesta: “No está en las fuentes”, sin añadir nada"))),
                     tarjeta(h5("Los 13 documentos"), p(class = "menudo", "Almeida et al. (2024) · Charnes et al. (1978) · Galvis-Aponte (2015) · Marques et al. (2020) · Maza Ávila et al. (2017) · Melo-Becerra et al. (2017) · Morales-Piñero et al. (2022) · Navarro Chávez et al. (2016) · Parteka y Wolszczak-Derlacz (2013) · Rincón-Chaparro y Romero-Bolívar (2025) · Simar y Wilson (1998) · Vázquez Rojas y Pérez-Esparrells (2016) · Visbal-Cadavid et al. (2017)"))),
      h5(class = "mt-4", "El recorrido"),
      div(class = "linea", span("Frase del anteproyecto"), span("Fila de la tabla (T01)"), span("Documento (galvis-aponte-2015)"), span("Página (p. 89)")),
      p(class = "menudo mt-2", "NotebookLM muestra el párrafo, pero no el número de página. La página la pone la tabla, revisada por una persona."),
      fte("README del corpus · protocolo de consulta v2 · tabla de trazabilidad.")),
  
  pan(5, h2("La evaluación"),
      p(class = "mt-3", "22 preguntas = 19 con respuesta conocida y localizada + 3 trampa (sin respuesta en ningún documento). Las mismas preguntas al sistema y a un chat sin documentos."),
      layout_columns(col_widths = c(6, 6),
                     cifra("18 de 19 frente a 2 de 19", "respuestas correctas: nuestro sistema frente al chat sin documentos", mar, "circle-check"),
                     cifra("3 de 3 frente a 2 de 3", "preguntas trampa: el sistema reconoció 3 de 3 que no tenía el dato; el chat, 2 de 3", mar, "scale-balanced")),
      tarjeta(class = "mt-3", h5("¿Cuántas universidades aparecen en el informe de ejecución del Portal de Transparencia Económica de 2024?"),
              actionButton("revela", "Ver las respuestas", class = "btn-primary mb-2"), uiOutput("q21")),
      layout_columns(col_widths = c(6, 6), class = "mt-3",
                     tarjeta(h5("Cómo falla el chat: números creíbles, pero falsos"),
                             tabla(data.frame(Chat = c("67 %", "159 instituciones"), `En lugar de` = c("63,43", "266"), check.names = FALSE))),
                     tarjeta(h5("Dónde falla nuestro sistema"),
                             tags$ul(tags$li("Al reconocer que no tenía un dato, añadió información que nadie le pidió, y ahí se equivocó: dijo 2019 donde el estudio dice 2018."),
                                     tags$li("Una respuesta correcta llegó sin cita.")),
                             p(strong("→ Cambio en las instrucciones: "), "citar cada oración y, cuando no sepa, responder solo eso."))),
      fte("Banco_Evaluacion_Final.xlsx, hojas Resultados y Corrida · protocolo de consulta v2.")),
  
  pan(6, h2("Límites y lo que no delegamos"),
      layout_columns(col_widths = c(6, 6), class = "mt-3",
                     tarjeta(h5("Lo que no pudimos hacer"),
                             tags$ul(tags$li("No siempre cada uno evaluó respuestas de artículos que no había verificado.")),
                             hr(), h5("Herramientas usadas"), p("NotebookLM, Consensus, ChatGPT, Gemini y Claude (apoyo en la redacción de documentos).")),
                     tarjeta(h5("Las 6 afirmaciones corregidas del anteproyecto"),
                             tags$ol(tags$li("La cifra de eficiencia en cobertura de Galvis-Aponte"), tags$li("Las páginas de la referencia de Galvis-Aponte"),
                                     tags$li("La descripción del modelo de Maza Ávila"), tags$li("Una restricción que Melo-Becerra no dice"),
                                     tags$li("El papel de la región en Morales-Piñero"), tags$li("Una afirmación sobre autocorrelación espacial sin ninguna cita")),
                             p(class = "menudo", "Tres artículos que se contradicen a sí mismos: Galvis-Aponte, Maza Ávila y Melo-Becerra."))),
      div(class = "destacado mt-3", strong("Lo que no delegamos: "), "abrir el documento y confirmar la página. Cada fila de la tabla la firmó quien abrió el artículo."),
      p(class = "cierre mt-5", "“Tener los documentos cargados no elimina el riesgo de que la IA invente: solo lo mueve. Ya no inventa referencias, pero puede inventar en lo que añade por su cuenta. Por eso la última palabra la tiene quien abre el documento.”"),
      fte("tabla de trazabilidad · memoria, apartados 5 y 6."))
)

# ---- Servidor ---------------------------------------------------------
server <- function(input, output, session) {
  patron <- "^(santoto|logo_usta)\\.(png|jpe?g|svg|webp)$"
  logo_src <- reactive({
    f <- input$logo
    if (!is.null(f)) return(paste0("data:", f$type, ";base64,", jsonlite::base64_enc(readBin(f$datapath, "raw", file.size(f$datapath)))))
    g <- list.files("www", pattern = patron, ignore.case = TRUE)
    if (length(g)) g[1] else NULL
  })
  output$subir <- renderUI(if (!length(list.files("www", pattern = patron, ignore.case = TRUE)) && is.null(input$logo))
    fileInput("logo", NULL, buttonLabel = "Subir logo", placeholder = "", accept = "image/*", width = "180px"))
  output$logo_nav <- renderUI(if (!is.null(logo_src())) tags$img(src = logo_src(), height = 36))
  output$logo_pie <- renderUI(if (!is.null(logo_src())) tags$img(src = logo_src()))
  output$logo_hero <- renderUI(if (!is.null(logo_src())) tags$img(src = logo_src(), alt = "Universidad Santo Tomás") else tags$b("Universidad", tags$br(), "Santo Tomás"))
  lapply(seq_len(nrow(secc)), function(i) observeEvent(input[[paste0("ir", i)]], nav_select("nav", secc$t[i])))
  lapply(seq_len(nrow(secc)), function(i) {
    observeEvent(input[[paste0("sig", i)]], nav_select("nav", secc$t[i + 1]))
    observeEvent(input[[paste0("ant", i)]], nav_select("nav", secc$t[i - 1]))
  })
  
  base <- function(p) p |> layout(font = list(family = "Instrument Sans", color = tinta), separators = ",.", transition = list(duration = 500, easing = "cubic-in-out"),
                                  paper_bgcolor = "rgba(0,0,0,0)", plot_bgcolor = "rgba(0,0,0,0)", margin = list(t = 20, l = 150)) |>
    config(displayModeBar = FALSE)
  
  output$g_exp <- renderPlotly({
    d <- exp_df[3:1, ]
    if (input$vista_exp == "ic") {
      plot_ly(d, y = ~trat, x = ~p, type = "bar", orientation = "h", marker = list(color = c(mar, ambar, coral)),
              error_x = list(type = "data", symmetric = FALSE, array = ~hi - p, arrayminus = ~p - lo, color = tinta),
              text = ~lab, textposition = "inside", insidetextanchor = "start", textfont = list(color = "#fff"),
              hovertemplate = paste0("%{y}<br>%{text}<extra></extra>")) |>
        layout(xaxis = list(title = "% utilizables (IC 95 %, Wilson)", range = c(0, 100)), yaxis = list(title = "")) |> base()
    } else {
      plot_ly(d, y = ~trat, x = ~util, type = "bar", orientation = "h", name = "Utilizable", marker = list(color = mar)) |>
        add_trace(x = ~existe, name = "Existe pero no dice eso", marker = list(color = ambar)) |>
        add_trace(x = ~noexiste, name = "No existe", marker = list(color = coral)) |>
        layout(barmode = "stack", xaxis = list(title = "Referencias (de 15)"), yaxis = list(title = ""),
               legend = list(orientation = "h", y = -0.3)) |> base()
    }
  })
  
  output$q21 <- renderUI({
    req(input$revela)
    layout_columns(col_widths = c(4, 4, 4),
                   div(class = "paso ok", strong("Nuestro sistema: "), "“No está en las fuentes.”"),
                   div(class = "paso mal", strong("Chat sin documentos: "), "“32 universidades públicas.”"),
                   div(class = "paso", strong("Dato real: "), "34"))
  })
}

shinyApp(ui, server)