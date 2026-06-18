"""
Monitor de Enquadramento Midiático
==================================
Trabalho de Introdução à Programação - FGV

Este script utiliza Streamlit para construir uma aplicação simples que:
1. Coleta manchetes de RSS Feeds de grandes portais brasileiros.
2. Processa os dados com Pandas (limpeza de texto e filtragem).
3. Realiza análise de sentimento com um léxico simples em português.
4. Exibe tabela interativa, gráfico de sentimentos e nuvem de palavras.

O objetivo é ser didático, mostrando loops, condicionais, manipulação de strings
e uso de bibliotecas populares sem depender de modelos complexos de NLP.
"""

import re
from datetime import datetime
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


import pandas as pd
import streamlit as st
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitor de Enquadramento Midiático", layout="wide")

POSITIVAS = {
    "bom", "boa", "bons", "boas", "ótimo", "ótima", "excelente", "positivo",
    "positiva", "sucesso", "avanço", "avançar", "prosperidade", "crescer",
    "crescimento", "feliz", "alegre", "confiança", "fortalecer", "melhorar",
    "melhoria", "eficiente", "capacidade", "oportunidade", "ganho", "superar",
    "vencer", "benefício", "vantagem", "recuperação", "recuperar", "inovação",
    "progresso", "sustentável", "esperança", "unir", "paz", "estabilidade",
    "segurança", "saúde", "educação", "emprego", "empregos", "alta", "cresce",
    "aumento", "aumentar", "reforçar", "celebrar", "conquista", "apoiar",
    "garantir", "resolver", "solução", "resultado", "resultados", "avançam"
}

NEGATIVAS = {
    "mau", "ruim", "ruins", "péssimo", "péssima", "terrível", "horrível",
    "negativo", "negativa", "fracasso", "crise", "crítica", "problema",
    "problemas", "dificuldade", "dificuldades", "queda", "cair", "diminuir",
    "redução", "perda", "perder", "falta", "falhar", "falha", "corrupção",
    "corrupto", "corrupta", "desemprego", "inflação", "pobreza", "violência",
    "crime", "criminoso", "guerra", "conflito", "ataque", "ataques",
    "tragedia", "tragédia", "desastre", "acidente", "morte", "mortes",
    "doença", "doenças", "pandemia", "demissão", "demissões", "greve",
    "manifestação", "protesto", "escândalo", "polemica", "polêmica",
    "tensão", "risco", "ameaça", "desmatamento", "desigualdade", "cortar",
    "corte", "aumentar", "insegurança", "déficit", "dívida", "fracassar",
    "colapso", "recessão", "depressão", "triste", "raiva", "ódio", "medo"
}

NEUTRAS = {
    "anuncia", "anunciar", "apresenta", "apresentar", "discute", "discutir",
    "debate", "debater", "aprovado", "aprovada", "rejeitado", "rejeitada",
    "sancionado", "sancionada", "publicado", "publicada", "lançado", "lançada",
    "reunião", "reuniões", "declaração", "entrevista", "reportagem", "notícia",
    "informação", "dado", "dados", "estudo", "pesquisa", "projeto", "proposta",
    "programa", "política", "economia", "sociedade", "governo", "mercado",
    "empresa", "empresas", "povo", "país", "brasil", "mundial", "nacional",
    "estadual", "municipal", "eleições", "eleitor", "candidato", "candidata",
    "partido", "congresso", "senado", "câmara", "stf", "ministério", "tribunal"
}

FEEDS = {
    "G1": "https://g1.globo.com/rss/g1/",
    "Folha de S.Paulo": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
    "Estadão": "https://www.estadao.com.br/rss/geral.xml"
}

def coletar_noticias(portais_selecionados):
    """
    Coleta notícias dos RSS feeds selecionados.

    Parâmetros:
        portais_selecionados (list): lista de nomes de portais escolhidos pelo usuário.

    Retorna:
        list: lista de dicionários com título, link, portal e data.
    """
    noticias = [] 

    for portal in portais_selecionados:
        url = FEEDS.get(portal)  
        if not url:
            continue 

        try:
            
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resposta:
                dados = resposta.read()

            
            raiz = ET.fromstring(dados)

            
            itens = raiz.findall(".//item")

            for item in itens:
                
                titulo = item.find("title")
                link = item.find("link")
                data = item.find("pubDate")

                
                if titulo is None or not titulo.text:
                    continue

                noticias.append({
                    "portal": portal,
                    "titulo": titulo.text.strip(),
                    "link": link.text.strip() if link is not None and link.text else "",
                    "data": data.text.strip() if data is not None and data.text else str(datetime.now()),
                    "coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        except urllib.error.URLError as erro:
          
            noticias.append({
                "portal": portal,
                "titulo": f"Erro ao acessar feed: {str(erro)}",
                "link": "",
                "data": str(datetime.now()),
                "coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as erro:
            
            noticias.append({
                "portal": portal,
                "titulo": f"Erro inesperado: {str(erro)}",
                "link": "",
                "data": str(datetime.now()),
                "coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return noticias



def limpar_texto(texto):
    """
    Limpa o texto para análise:
    - Converte para minúsculas.
    - Remove pontuação com expressão regular.
    - Remove espaços extras.
    """
    if not isinstance(texto, str):
        return ""

    texto = texto.lower()  # Minúsculas para comparação uniforme.
    
    texto = re.sub(r"[^a-zà-úçõãáéíóúâêô0-9\s]", " ", texto)
    
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def filtrar_por_palavra_chave(df, palavra_chave):
    """
    Filtra o DataFrame mantendo apenas linhas cujo título limpo contém a palavra-chave.

    Parâmetros:
        df (DataFrame): tabela de notícias.
        palavra_chave (str): termo digitado pelo usuário.

    Retorna:
        DataFrame filtrado.
    """
    if not palavra_chave or not palavra_chave.strip():
        return df  # Se não houver palavra-chave, retorna tudo.

    chave_limpa = limpar_texto(palavra_chave)
    
    mascara = df["titulo_limpo"].str.contains(chave_limpa, na=False)
    return df[mascara].copy()


def analisar_sentimento(texto):
    """
    Classifica o texto em Positivo, Negativo ou Neutro com base na contagem de
    palavras presentes nos léxicos POSITIVAS, NEGATIVAS e NEUTRAS.

    A lógica é didática e explícita:
    1. Separa o texto em palavras.
    2. Para cada palavra, verifica se pertence a algum conjunto de sentimento.
    3. Conta as ocorrências.
    4. Compara os totais e decide o sentimento predominante.
    """
    if not texto:
        return "Neutro", 0, 0, 0

    palavras = texto.split()

    positivo = 0
    negativo = 0
    neutro = 0

    
    for palavra in palavras:
        if palavra in POSITIVAS:
            positivo += 1
        elif palavra in NEGATIVAS:
            negativo += 1
        elif palavra in NEUTRAS:
            neutro += 1

    
    if positivo > negativo and positivo > neutro:
        return "Positivo", positivo, negativo, neutro
    elif negativo > positivo and negativo > neutro:
        return "Negativo", positivo, negativo, neutro
    else:
        return "Neutro", positivo, negativo, neutro



def gerar_nuvem(texto_completo):
    """
    Gera uma imagem de nuvem de palavras a partir de um texto.
    Filtra palavras muito curtas e remove stopwords simples em português.
    """
    # Stopwords básicas em português para não poluir a nuvem.
    stopwords_pt = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com",
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos",
        "como", "mas", "ao", "ele", "das", "à", "seu", "sua", "ou", "quando",
        "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até",
        "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "ter", "seus",
        "quem", "nas", "me", "esse", "eles", "você", "essa", "num", "nem",
        "suas", "meu", "às", "minha", "têm", "numa", "pelos", "elas", "qual",
        "lhe", "deles", "delas", "uma", "nessa", "nesta", "em", "para", "como",
        "sobre", "após", "ante", "até", "conforme", "contra", "desde", "durante",
        "entre", "excepto", "mediante", "perante", "por", "sem", "sob", "sobre",
        "trás", "versus", "via", "rs", "re", "diz", "dizem", "afirma", "afirmam"
    }

    
    palavras = limpar_texto(texto_completo).split()
    palavras_filtradas = [p for p in palavras if len(p) > 3 and p not in stopwords_pt]
    texto_filtrado = " ".join(palavras_filtradas)

    if not texto_filtrado.strip():
        return None

    
    nuvem = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=100,
        colormap="viridis"
    ).generate(texto_filtrado)

    return nuvem




def main():
    """
    Função principal que monta a interface e organiza a execução do app.
    """
    
    st.title("📰 Monitor de Enquadramento Midiático")
    st.markdown(
        """
        Este painel coleta manchetes de grandes portais de notícias, permite filtrar
        por palavra-chave e realiza uma **análise de sentimento didática** com base
        em um léxico simples de palavras em português.
        """
    )

    
    st.sidebar.header("⚙️ Filtros")

    
    portais_disponiveis = list(FEEDS.keys())
    portais_selecionados = st.sidebar.multiselect(
        "Selecione os portais:",
        options=portais_disponiveis,
        default=portais_disponiveis
    )

    
    palavra_chave = st.sidebar.text_input(
        "Palavra-chave para filtrar:",
        value="Brasil",
        help="Digite um termo para filtrar as manchetes coletadas."
    )

    
    botao_coletar = st.sidebar.button("🔄 Coletar notícias")

    st.sidebar.markdown("---")
    st.sidebar.info(
        "Dica: a análise de sentimento é didática e usa contagem de palavras. "
        "Ela não substitui modelos avançados de NLP, mas ilustra bem lógica de programação."
    )

   
    if botao_coletar and portais_selecionados:
        with st.spinner("Coletando manchetes dos portais..."):
            noticias = coletar_noticias(portais_selecionados)

        if not noticias:
            st.warning("Nenhuma notícia foi coletada. Verifique os feeds selecionados.")
            return

        
        df = pd.DataFrame(noticias)

        
        df["titulo_limpo"] = df["titulo"].apply(limpar_texto)

       
        df_filtrado = filtrar_por_palavra_chave(df, palavra_chave)

        
        resultados = df_filtrado["titulo_limpo"].apply(analisar_sentimento)

        
        df_filtrado["sentimento"] = resultados.apply(lambda x: x[0])
        df_filtrado["positivas"] = resultados.apply(lambda x: x[1])
        df_filtrado["negativas"] = resultados.apply(lambda x: x[2])
        df_filtrado["neutras"] = resultados.apply(lambda x: x[3])

        
        aba_tabela, aba_grafico, aba_nuvem = st.tabs(
            ["📋 Tabela", "📊 Sentimentos", "☁️ Nuvem de Palavras"]
        )

       
        with aba_tabela:
            st.subheader("Notícias filtradas")

            st.markdown(f"**Total de notícias encontradas:** {len(df_filtrado)}")
            st.markdown(
                f"**Coletadas em:** {df_filtrado['coleta'].iloc[0] if len(df_filtrado) > 0 else '-' }"
            )

            if df_filtrado.empty:
                st.warning("Nenhuma notícia corresponde à palavra-chave informada.")
            else:
                
                st.dataframe(
                    df_filtrado[["portal", "titulo", "sentimento", "data", "link"]].reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )

                
                csv = df_filtrado.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Baixar dados filtrados (CSV)",
                    data=csv,
                    file_name="noticias_filtradas.csv",
                    mime="text/csv"
                )

        
        with aba_grafico:
            st.subheader("Distribuição de sentimentos")

            if df_filtrado.empty:
                st.warning("Não há dados para gerar o gráfico.")
            else:
                
                contagem = df_filtrado["sentimento"].value_counts().reset_index()
                contagem.columns = ["sentimento", "quantidade"]

               
                for categoria in ["Positivo", "Neutro", "Negativo"]:
                    if categoria not in contagem["sentimento"].values:
                        contagem = pd.concat(
                            [contagem, pd.DataFrame({"sentimento": [categoria], "quantidade": [0]})],
                            ignore_index=True
                        )

                
                cores = {"Positivo": "green", "Neutro": "gray", "Negativo": "red"}
                contagem["cor"] = contagem["sentimento"].map(cores)

                
                fig = px.bar(
                    contagem,
                    x="sentimento",
                    y="quantidade",
                    color="sentimento",
                    color_discrete_map=cores,
                    labels={"sentimento": "Sentimento", "quantidade": "Quantidade de notícias"},
                    title="Quantidade de notícias por sentimento"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

                
                col1, col2, col3 = st.columns(3)
                total_pos = int(df_filtrado["positivas"].sum())
                total_neg = int(df_filtrado["negativas"].sum())
                total_neu = int(df_filtrado["neutras"].sum())

                col1.metric("Palavras positivas", total_pos)
                col2.metric("Palavras neutras", total_neu)
                col3.metric("Palavras negativas", total_neg)

        
        with aba_nuvem:
            st.subheader("Nuvem de palavras das manchetes")

            if df_filtrado.empty:
                st.warning("Não há textos para gerar a nuvem de palavras.")
            else:
                
                texto_nuvem = " ".join(df_filtrado["titulo_limpo"].tolist())
                nuvem = gerar_nuvem(texto_nuvem)

                if nuvem is None:
                    st.warning("Texto insuficiente para gerar a nuvem de palavras.")
                else:
                   
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(nuvem, interpolation="bilinear")
                    ax.axis("off")  # Remove os eixos para uma imagem mais limpa.
                    st.pyplot(fig)

    else:
       
        st.info(
            "👈 Use a barra lateral para selecionar portais e definir uma palavra-chave, "
            "depois clique em **Coletar notícias** para iniciar a análise."
        )


