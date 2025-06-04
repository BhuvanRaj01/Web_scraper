import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime
from scraper import (
    fetch_html_selenium,
    save_raw_data,
    format_data,
    save_formatted_data,
    calculate_price,
    html_to_markdown_with_readability,
    create_dynamic_listing_model,
    create_listings_container_model
)

# App Configuration
st.set_page_config(
    page_title="Scrape-Wise",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App Title and Description
st.markdown(
    """
    <div style="animation: fadeIn 2s; text-align: center; margin-bottom: 20px;">
        <h1>Scrape-Wise 🔧</h1>
        <h3>Effortlessly scrape and format web data with ease</h3>
        <p style="font-size: 1.1em;">
            Scrape-Wise simplifies web scraping with customizable field extraction and
            dynamic data formatting. Input your URL, define your fields, and let us do the rest!
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar Components
st.sidebar.markdown(
    """
    <div style="animation: slideInLeft 1.5s;">
        <h2>Web Scraper Settings</h2>
        <p>Configure the settings below to get started.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Model Selection
model_selection = st.sidebar.selectbox(
    "Select AI Model",
    options=["gpt-4o-mini", "gpt-4o-2024-08-06"],
    index=0
)

# URL Input
url_input = st.sidebar.text_input("Enter the URL to scrape")

# Tags Input for Field Extraction
tags = st_tags_sidebar(
    label='Fields to Extract:',
    text='Press enter to add a tag',
    value=[],
    suggestions=[],
    maxtags=-1,
    key='tags_input'
)
st.sidebar.markdown("---")

# Process Tags
fields = tags

# Token and Cost Information
input_tokens = output_tokens = total_cost = 0

# Define Scraping Function
def perform_scrape():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_html = fetch_html_selenium(url_input)
    markdown = html_to_markdown_with_readability(raw_html)
    save_raw_data(markdown, timestamp)
    
    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
    
    formatted_data = format_data(markdown, DynamicListingsContainer)
    formatted_data_text = json.dumps(formatted_data.dict())
    
    input_tokens, output_tokens, total_cost = calculate_price(
        markdown, formatted_data_text, model=model_selection
    )
    df = save_formatted_data(formatted_data, timestamp)

    return df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp

# Button to Trigger Scraping
if 'perform_scrape' not in st.session_state:
    st.session_state['perform_scrape'] = False

if st.sidebar.button("Scrape Data"):
    if not url_input:
        st.sidebar.error("Please enter a valid URL to scrape.")
    else:
        with st.spinner('Scraping data, please wait...'):
            st.session_state['results'] = perform_scrape()
            st.session_state['perform_scrape'] = True

# Display Results
if st.session_state.get('perform_scrape'):
    with st.container():
        st.markdown(
            """
            <div style="animation: fadeIn 1.5s;">
                <h3>Scraped Data</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Data", expanded=True):
            df, formatted_data, markdown, input_tokens, output_tokens, total_cost, timestamp = st.session_state['results']
            st.dataframe(df, use_container_width=True)

    # Animated Token Usage Summary
    with st.sidebar:
        st.markdown(
            """
            <div style="animation: fadeIn 2s;">
                <h3>Token Usage</h3>
                <p><strong>Input Tokens:</strong> {}</p>
                <p><strong>Output Tokens:</strong> {}</p>
                <p><strong>Total Cost:</strong> <span style="color: green;">${:.4f}</span></p>
            </div>
            """.format(input_tokens, output_tokens, total_cost),
            unsafe_allow_html=True
        )

    # Download Options
    st.markdown("### Download Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download JSON",
            data=json.dumps(formatted_data.dict(), indent=4),
            file_name=f"{timestamp}_data.json"
        )

    with col2:
        data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data
        first_key = next(iter(data_dict))
        main_data = data_dict[first_key]
        df_csv = pd.DataFrame(main_data)

        st.download_button(
            "Download CSV",
            data=df_csv.to_csv(index=False),
            file_name=f"{timestamp}_data.csv"
        )

    with col3:
        st.download_button(
            "Download Markdown",
            data=markdown,
            file_name=f"{timestamp}_data.md"
        )

# Footer
st.sidebar.markdown("---")

# Add CSS Animations
st.markdown(
    """
    <style>
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .stSidebar div, .stExpander div, .stContainer div { animation: fadeIn 1.5s ease-in; }
    </style>
    """,
    unsafe_allow_html=True
)