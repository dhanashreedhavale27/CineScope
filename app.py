import ast
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# CineScope - OTT Platform and Streaming Content Analytics
st.set_page_config(page_title="CineScope - OTT Analytics", page_icon="🎬", layout="wide")

# Bright, high-contrast dashboard styling
st.markdown("""<style>
    .stApp { background: linear-gradient(135deg, #f4f7ff 0%, #eef2ff 55%, #fdf2f8 100%); color: #172554; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #312e81 0%, #4c1d95 100%); }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input { color: #172554 !important; }
    .stApp, .stApp p, .stApp label, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3 { color: #172554; }
    .stApp h1 { color: #312e81 !important; font-weight: 800; }
    .stApp h2, .stApp h3 { color: #4338ca !important; }
    [data-testid="stMetric"] { background: #ffffff; border: 1px solid #c7d2fe; border-left: 5px solid #7c3aed; padding: 16px; border-radius: 14px; box-shadow: 0 3px 12px rgba(49, 46, 129, 0.10); }
    [data-testid="stMetricLabel"] { color: #475569 !important; }
    [data-testid="stMetricValue"] { color: #6d28d9 !important; font-weight: 800; }
    button[data-baseweb="tab"] { color: #4338ca !important; font-weight: 700; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #be185d !important; border-bottom: 3px solid #ec4899 !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { background: #ffffff; border-radius: 10px; }
    .stTextInput input { background: #ffffff; color: #172554; border: 1px solid #a5b4fc; }
    .stAlert { border-radius: 10px; }
    .stDownloadButton button { background: #6d28d9; color: #ffffff; border: 0; border-radius: 8px; font-weight: 700; }
    .stDownloadButton button:hover { background: #be185d; color: #ffffff; }
    [data-testid="stExpander"] { background: #ffffff; border: 1px solid #c7d2fe; border-radius: 10px; }
</style>""", unsafe_allow_html=True)

# Load both CSV files
@st.cache_data
def load_data():
    titles = pd.read_csv("titles_dataset.csv").drop_duplicates(subset="id").dropna(subset=["title"])
    credits = pd.read_csv("ott_dataset.csv").drop_duplicates()

    num_cols = ["release_year", "runtime", "seasons", "imdb_score", "imdb_votes", "tmdb_popularity", "tmdb_score"]
    titles[num_cols] = titles[num_cols].apply(pd.to_numeric, errors="coerce")

    def convert_to_list(value):
        if pd.isna(value) or not str(value).strip(): return []
        try:
            result = ast.literal_eval(str(value))
            return result if isinstance(result, list) else [str(result)]
        except (ValueError, SyntaxError):
            return [item.strip() for item in str(value).split(",") if item.strip()]

    titles["genre_list"] = titles["genres"].apply(convert_to_list)
    titles["country_list"] = titles["production_countries"].apply(convert_to_list)
    credits["name"] = credits["name"].fillna("Unknown")
    credits["role"] = credits["role"].fillna("Unknown").str.upper()
    return titles, credits

try:
    titles, credits = load_data()
except FileNotFoundError:
    st.error("CSV files not found. Keep titles_dataset.csv and ott_dataset.csv in the same folder as app.py.")
    st.stop()

# Consistent bright colours for Matplotlib charts
CHART_COLORS = ["#7c3aed", "#ec4899", "#06b6d4", "#f59e0b", "#10b981", "#3b82f6", "#f97316", "#8b5cf6", "#14b8a6", "#e11d48"]
plt.rcParams.update({
    "figure.facecolor": "#ffffff", "axes.facecolor": "#f8fafc", "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#1e293b", "xtick.color": "#334155", "ytick.color": "#334155",
    "text.color": "#1e293b", "axes.titlecolor": "#312e81", "grid.color": "#cbd5e1", "font.size": 10
})

def show_plot(fig):
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# SIDEBAR FILTERS
st.sidebar.title("CineScope")
st.sidebar.write("OTT Content Analytics")
st.sidebar.markdown("---")
st.sidebar.subheader("Filter the Dataset")

content_options = ["All"] + sorted(titles["type"].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("Content Type", content_options)

min_year, max_year = int(titles["release_year"].min()), int(titles["release_year"].max())
selected_years = st.sidebar.slider("Release Year Range", min_year, max_year, (max(min_year, 2000), max_year))

all_genres = sorted({genre for glist in titles["genre_list"] for genre in glist})
selected_genres = st.sidebar.multiselect("Select Genres", all_genres)

all_countries = sorted({country for clist in titles["country_list"] for country in clist})
selected_countries = st.sidebar.multiselect("Select Production Countries", all_countries)

valid_ratings = titles["imdb_score"].dropna()
min_r, max_r = (float(valid_ratings.min()), float(valid_ratings.max())) if len(valid_ratings) else (0.0, 10.0)
selected_rating = st.sidebar.slider("Minimum IMDb Rating", min_r, max_r, min_r, step=0.1)

# APPLY FILTERS
filtered = titles[
    titles["release_year"].between(selected_years[0], selected_years[1]) &
    (titles["imdb_score"].isna() | (titles["imdb_score"] >= selected_rating))
]
if selected_type != "All":
    filtered = filtered[filtered["type"] == selected_type]
if selected_genres:
    filtered = filtered[filtered["genre_list"].apply(lambda items: any(genre in items for genre in selected_genres))]
if selected_countries:
    filtered = filtered[filtered["country_list"].apply(lambda items: any(country in items for country in selected_countries))]

filtered_credits = credits[credits["id"].isin(set(filtered["id"]))].copy()

# MAIN PAGE
st.title("CineScope")
st.subheader("Explore. Analyse. Discover.")
st.write("An interactive dashboard to explore movies, TV shows, genres, ratings, popularity and OTT content trends.")
st.markdown("---")

if filtered.empty:
    st.warning("No records found. Please change the filters.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Overview", "Dataset Explorer", "Visualizations", "Insights and Credits"])

# TAB 1 - DASHBOARD OVERVIEW
with tab1:
    st.header("Dashboard Overview")
    total_titles = len(filtered)
    total_movies = (filtered["type"] == "MOVIE").sum()
    total_shows = (filtered["type"] == "SHOW").sum()
    avg_rating, avg_runtime = filtered["imdb_score"].mean(), filtered["runtime"].mean()
    director_count = filtered_credits[filtered_credits["role"] == "DIRECTOR"]["name"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Titles", f"{total_titles:,}")
    col2.metric("Movies", f"{total_movies:,}")
    col3.metric("TV Shows", f"{total_shows:,}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Average IMDb Rating", f"{avg_rating:.2f}/10" if pd.notna(avg_rating) else "N/A")
    col5.metric("Average Runtime", f"{avg_runtime:.1f} minutes" if pd.notna(avg_runtime) else "N/A")
    col6.metric("Unique Directors", f"{director_count:,}")

    st.markdown("---")
    st.subheader("Movies and TV Shows Distribution")
    type_counts = filtered["type"].value_counts()
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.pie(type_counts.values, labels=type_counts.index, colors=CHART_COLORS[:len(type_counts)], autopct="%1.1f%%", startangle=90)
    ax1.set_title("Movies vs TV Shows")
    show_plot(fig1)

    with st.expander("View Statistical Summary"):
        st.write(filtered[["release_year", "runtime", "imdb_score", "imdb_votes", "tmdb_popularity", "tmdb_score"]].describe().round(2))

# TAB 2 - DATASET EXPLORER
with tab2:
    st.header("Explore OTT Dataset")
    search_title = st.text_input("Search for a movie or TV show")
    display_data = filtered[filtered["title"].str.contains(search_title, case=False, na=False)] if search_title else filtered.copy()
    columns_to_show = ["title", "type", "release_year", "age_certification", "runtime", "genres", "production_countries", "imdb_score", "tmdb_score", "tmdb_popularity"]

    st.write("Number of matching records:", len(display_data))
    st.dataframe(display_data[columns_to_show], use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", display_data[columns_to_show].to_csv(index=False), "cinescope_filtered_data.csv", "text/csv")

# TAB 3 - DATA VISUALIZATIONS
with tab3:
    st.header("Data Visualizations")

    # BAR CHART - Top 10 Genres
    st.subheader("1. Bar Chart - Top 10 Genres")
    genre_data = filtered["genre_list"].explode().dropna()
    genre_counts = genre_data.value_counts().head(10)
    if len(genre_counts) > 0:
        fig2, ax2 = plt.subplots(figsize=(9, 5))
        ax2.barh(genre_counts.index[::-1], genre_counts.values[::-1], color=CHART_COLORS[:len(genre_counts)][::-1])
        ax2.set(title="Top 10 Genres by Number of Titles", xlabel="Number of Titles", ylabel="Genre")
        ax2.grid(axis="x", linestyle="--", alpha=0.4)
        show_plot(fig2)
        st.write("Observation: The bar chart compares the number of titles available in each of the most common genres.")
    else:
        st.info("Genre data is not available for these filters.")

    st.markdown("---")
    # LINE CHART - Releases by Year
    st.subheader("2. Line Chart - OTT Releases Over the Years")
    yearly_data = filtered.groupby("release_year").size().reset_index(name="number_of_titles").sort_values("release_year")
    fig3, ax3 = plt.subplots(figsize=(9, 5))
    ax3.plot(yearly_data["release_year"], yearly_data["number_of_titles"], marker="o", linewidth=2, color="#7c3aed", markerfacecolor="#ec4899")
    ax3.set(title="Number of Titles Released Each Year", xlabel="Release Year", ylabel="Number of Titles")
    ax3.grid(True, linestyle="--", alpha=0.4)
    show_plot(fig3)
    st.write("Observation: The line chart shows how the number of titles in the dataset changes across release years.")

    st.markdown("---")
    # SCATTER PLOT - IMDb Rating vs TMDB Popularity
    st.subheader("3. Scatter Plot - IMDb Rating vs TMDB Popularity")
    scatter_data = filtered.dropna(subset=["imdb_score", "tmdb_popularity"])
    if len(scatter_data) > 0:
        fig4, ax4 = plt.subplots(figsize=(9, 5))
        for content_type in scatter_data["type"].dropna().unique():
            group = scatter_data[scatter_data["type"] == content_type]
            ax4.scatter(group["imdb_score"], group["tmdb_popularity"], label=content_type, alpha=0.7, color="#7c3aed" if content_type == "MOVIE" else "#ec4899")
        ax4.set(title="IMDb Rating vs TMDB Popularity", xlabel="IMDb Rating", ylabel="TMDB Popularity")
        ax4.legend(title="Content Type")
        ax4.grid(True, linestyle="--", alpha=0.4)
        show_plot(fig4)
        st.write("Observation: Each point represents a title. The scatter plot helps examine the relationship between IMDb rating and TMDB popularity.")
    else:
        st.info("Not enough rating and popularity values for the scatter plot.")

# TAB 4 - INSIGHTS AND CREDITS
with tab4:
    st.header("Insights and Credits Analysis")
    genre_data = filtered["genre_list"].explode().dropna()
    if not genre_data.empty:
        genre_counts = genre_data.value_counts()
        st.write("**Most common genre:**", genre_counts.index[0], "-", int(genre_counts.iloc[0]), "title-genre entries")

    country_data = filtered["country_list"].explode().dropna()
    if not country_data.empty:
        country_counts = country_data.value_counts()
        st.write("**Top production country:**", country_counts.index[0], "-", int(country_counts.iloc[0]), "title-country entries")
        top_countries = country_counts.head(10)
        fig5, ax5 = plt.subplots(figsize=(9, 5))
        ax5.bar(top_countries.index, top_countries.values, color=CHART_COLORS[:len(top_countries)])
        ax5.set(title="Top 10 Production Countries", xlabel="Country", ylabel="Number of Titles")
        ax5.tick_params(axis="x", rotation=45)
        ax5.grid(axis="y", linestyle="--", alpha=0.4)
        show_plot(fig5)

    st.markdown("---")
    st.subheader("Cast and Director Analysis")
    selected_role = st.selectbox("Select Role", ["ACTOR", "DIRECTOR"])
    role_data = filtered_credits[filtered_credits["role"] == selected_role]
    people_counts = role_data["name"].value_counts().head(10)
    if not people_counts.empty:
        fig6, ax6 = plt.subplots(figsize=(9, 5))
        ax6.barh(people_counts.index[::-1], people_counts.values[::-1], color="#06b6d4")
        ax6.set(title="Top 10 " + selected_role.title() + "s by Credits", xlabel="Number of Credits", ylabel="Name")
        show_plot(fig6)
    else:
        st.info("No credits found for the selected role.")

    st.markdown("---")
    st.subheader("Top 10 Highest Rated Titles")
    top_rated = filtered.dropna(subset=["imdb_score"]).sort_values("imdb_score", ascending=False)[["title", "type", "release_year", "imdb_score", "imdb_votes"]].head(10)
    st.dataframe(top_rated, use_container_width=True, hide_index=True)

# FOOTER
st.markdown("---")
st.markdown("<center>CineScope | OTT Platform and Streaming Content Analytics Using Python</center>", unsafe_allow_html=True)
