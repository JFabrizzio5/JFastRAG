import requests
import json
import unicodedata
from difflib import SequenceMatcher

OLLAMA_URL = "http://localhost:11434/api/generate"

LIBROS = {
    "El Principito": [
        "Lo esencial es invisible a los ojos.",
        "Solo se ve bien con el corazón.",
        "Fue el tiempo que pasaste con tu rosa lo que la hizo tan importante.",
        "Todas las personas mayores fueron al principio niños, pero pocas lo recuerdan."
    ],
    "Viaje al Centro de la Tierra": [
        "La historia se desarrolla en Hamburgo, Alemania.",
        "El profesor Lidenbrock descubre un manuscrito rúnico antiguo.",
        "Viajan a Islandia para descender por un volcán hacia el centro de la Tierra."
    ],
    "Fundamentos de Astrofísica": [
        "Un agujero negro es una región del espacio con una concentración de masa elevada.",
        "Su campo gravitatorio es tan fuerte que ni la luz puede escapar.",
        "Esto se debe a la deformación extrema del espaciotiempo."
    ]
}

STOPWORDS = {'dime', 'algo', 'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se',
             'un', 'una', 'sobre', 'con', 'mi', 'al', 'lo', 'las', 'su', 'para', 'es',
             'eres', 'texto', 'tenga', 'referencias', 'quiero', 'sabes', 'me', 'cuenta'}

ultima_fuente = {"titulo": None, "paginas": []}


def normalizar(texto):
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower()


def tokenizar(texto):
    return {palabra for palabra in normalizar(texto).split() if palabra not in STOPWORDS}


def similitud(a, b):
    return SequenceMatcher(None, a, b).ratio()


def buscar_mejor_pagina(pregunta):
    tokens_pregunta = tokenizar(pregunta)

    mejor_puntaje = 0
    mejor_resultado = (None, None, None)

    for titulo, paginas in LIBROS.items():
        tokens_titulo = tokenizar(titulo)

        for idx, contenido in enumerate(paginas):
            tokens_contenido = tokenizar(contenido)

            coincidencias = sum(
                1 for token in tokens_pregunta
                if any(similitud(token, t) > 0.8 for t in tokens_contenido.union(tokens_titulo))
            )

            if normalizar(titulo) in normalizar(pregunta):
                coincidencias += 2

            if coincidencias > mejor_puntaje:
                mejor_puntaje = coincidencias
                mejor_resultado = (titulo, idx + 1, contenido)

    return mejor_resultado if mejor_puntaje > 0 else (None, None, None)


def buscar_similares_en_varios_libros(pregunta, min_similitud=1):
    tokens_pregunta = tokenizar(pregunta)
    resultados = []

    for titulo, paginas in LIBROS.items():
        tokens_titulo = tokenizar(titulo)

        for idx, contenido in enumerate(paginas):
            tokens_contenido = tokenizar(contenido)

            coincidencias = sum(
                1 for token in tokens_pregunta
                if any(similitud(token, t) > 0.8 for t in tokens_contenido.union(tokens_titulo))
            )

            if coincidencias >= min_similitud:
                resultados.append((coincidencias, titulo, idx + 1, contenido))

    resultados.sort(reverse=True)
    return resultados[:3]  # Top 3 coincidencias


def buscar_libro_completo(pregunta):
    for titulo in LIBROS:
        if normalizar(titulo) in normalizar(pregunta):
            return titulo
    return None


def resumir_libro(titulo, pregunta):
    contenido = "\n".join(LIBROS[titulo])
    prompt = f"""
Eres un asistente de investigación que solo responde con base en el contenido proporcionado.
NO uses conocimiento externo. NO inventes nada.
Si no está en el texto, responde: "No se encuentra en el texto" PERO responde con una recomendación de lo más similar que encontraste en los textos disponibles.

Título: {titulo}
Texto completo:
{contenido}

Pregunta: {pregunta}

Respuesta:
"""
    payload = {"model": "llama3.1", "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, data=json.dumps(payload))
    respuesta = response.json()['response'].strip()

    return respuesta


def preguntar_al_investigador(pregunta):
    global ultima_fuente

    pregunta_normalizada = normalizar(pregunta)
    resumen_keywords = {'resumen', 'explica', 'como', 'qué', 'que', 'significa', 'por qué'}

    # 1. Si pide resumen de la última fuente
    if "ultima fuente" in pregunta_normalizada and ultima_fuente["titulo"]:
        titulo = ultima_fuente["titulo"]
        resumen = resumir_libro(titulo, pregunta)
        print(f"🤖 Respuesta: {resumen} \n📖 Fuente: {titulo} (todo el libro)")
        return

    # 2. Si menciona un libro directamente y pregunta algo general
    libro_mencionado = buscar_libro_completo(pregunta)
    if libro_mencionado and any(k in pregunta_normalizada for k in resumen_keywords):
        ultima_fuente["titulo"] = libro_mencionado
        ultima_fuente["paginas"] = LIBROS[libro_mencionado]
        resumen = resumir_libro(libro_mencionado, pregunta)
        print(f"🤖 Respuesta: {resumen} \n📖 Fuente: {libro_mencionado} (todo el libro)")
        return

    # 3. Buscar mejor página específica
    titulo, pagina, texto = buscar_mejor_pagina(pregunta)

    if not titulo:
        similares = buscar_similares_en_varios_libros(pregunta)
        if similares:
            print("🤖 No encontré una coincidencia exacta, pero aquí hay contenido similar:")
            for coincidencias, titulo, pagina, texto in similares:
                print(f"\n📖 Libro: {titulo}, Página: {pagina}")
                print(f"📝 Fragmento: \"{texto}\"")
            return
        else:
            print("🤖 Respuesta: Lo siento, no encontré ningún texto relevante en la base de conocimientos.")
            return

    ultima_fuente["titulo"] = titulo
    ultima_fuente["paginas"] = LIBROS[titulo]

    prompt = f"""
Eres un asistente de investigación que solo responde con base en el contenido proporcionado.
NO uses conocimiento externo. NO inventes.
Si no está en el texto, responde: "No se encuentra en el texto" pero si no responde con una recomendación de lo más similar que encontraste en los textos disponibles.

Libro: {titulo}, página {pagina}
Texto:
"{texto}"

Pregunta: {pregunta}

Respuesta:
"""
    payload = {"model": "llama3.1", "prompt": prompt, "stream": False}

    try:
        response = requests.post(OLLAMA_URL, data=json.dumps(payload))
        response.raise_for_status()
        respuesta = response.json()["response"].strip()
        print(f"🤖 Respuesta: {respuesta} \n📖 Fuente: {titulo}, página {pagina}")
    except Exception as e:
        print(f"Error al contactar a Ollama: {e}")


def resumir_conocimientos():
    print("🤖 Tengo información de los siguientes libros:\n")
    for titulo, paginas in LIBROS.items():
        print(f"📘 {titulo} ({len(paginas)} páginas):")
        for i, linea in enumerate(paginas, start=1):
            resumen = linea.strip()[:60] + ("..." if len(linea.strip()) > 60 else "")
            print(f"   - Página {i}: {resumen}")
    print("\nHazme preguntas sobre estos textos.")


# -------------------- MAIN LOOP --------------------
if __name__ == "__main__":
    print("🕵️‍♂️ Asistente de Investigación v3 (Conocimiento Cerrado)")
    print("Puedes preguntarme sobre el contenido de mis textos o escribir 'textos' para ver la base.")
    print("Escribe 'salir' para terminar.")
    print("-" * 50)

    while True:
        pregunta_usuario = input("👤 Tú: ").strip()
        pregunta_lower = normalizar(pregunta_usuario)

        if pregunta_lower == 'salir':
            print("👋 Cerrando archivo. ¡Hasta luego!")
            break
        elif any(cmd in pregunta_lower for cmd in ['textos', 'libros', 'conoces']):
            resumir_conocimientos()
        else:
            preguntar_al_investigador(pregunta_usuario)

        print("-" * 50)
