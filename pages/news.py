import streamlit as st
from exa_py import Exa
from dotenv import load_dotenv
import datetime
import requests
import os 

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
exa = Exa(api_key=os.getenv("EXA_API_KEY"))


def load_news():

    result = exa.search_and_contents(
        "srilankan politics",
        type="neural",
        use_autoprompt=True,
        num_results=10,
        text={
            "max_characters": 400
        },
        start_published_date=(datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(),
        end_published_date=datetime.datetime.now().isoformat()
    ).__dict__

    return result['results']

    
def display_news(articles):
    for article in articles:
        # Format the publication date
        pub_date = datetime.datetime.strptime(article.published_date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')

        # Create news card with author, title, description, and link
        st.markdown(f"""
            <div style='
                background-color:#2c2c2c;
                border-radius:10px;
                padding:15px;
                margin-bottom:15px;
                box-shadow:0px 4px 8px rgba(0, 0, 0, 0.6);
                color:#e0e0e0;
                '>
                <h3 style='color:#1a73e8;'>{article.title}</h3>
                <p><b>Published on:</b> {pub_date}</p>
                <p>{article.text}</p>
                <br>
                <p><b>Author:</b> {article.author}</p>
                <a href="{article.url}" target="_blank" style='text-decoration:none; color:#ff5733;'>
                    Read more
                </a>
            </div>
        """, unsafe_allow_html=True)


st.set_page_config(
    page_title="News", 
    page_icon="🧊", 
    layout="wide"
)

st.title("News")

# Subheading
st.subheader("Stay updated with the latest political news from Sri Lanka")

# Load news articles on page load
news_articles = load_news()

# Display news in a stylish format
if news_articles:
    display_news(news_articles)
else:
    st.write("No news articles found.")

# Footer
st.markdown("<hr><p style='text-align:center;'>Powered by NewsData.io</p>", unsafe_allow_html=True)
