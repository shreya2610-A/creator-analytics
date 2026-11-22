from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Creator Audience Analytics", layout="wide")
BASE = Path(__file__).parent


@st.cache_data
def load_data():
    audience = pd.read_csv(BASE / "audience.csv")
    content = pd.read_csv(BASE / "content.csv", parse_dates=["posting_date"])
    inter = pd.read_csv(BASE / "interactions.csv", parse_dates=["interaction_date"])
    # same as SQL JOINs: Interactions + Audience + Content
    df = inter.merge(audience, on="audience_id", how="left").merge(
        content, on="post_id", how="left"
    )
    df["month"] = df["interaction_date"].dt.to_period("M").astype(str)
    return audience, content, df


audience, content, df = load_data()

st.title("Creator Audience Analytics")
st.caption("Which content does which audience engage with? Use the filters on the left.")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")


def pick(label, col):
    options = sorted(df[col].dropna().unique())
    return st.sidebar.multiselect(label, options, default=options)


age = pick("Age group", "age_group")
loc = pick("Location", "location")
fol = pick("Follower status", "follower_status")
cat = pick("Content category", "content_category")
fmt = pick("Content format", "content_format")

f = df[
    df["age_group"].isin(age)
    & df["location"].isin(loc)
    & df["follower_status"].isin(fol)
    & df["content_category"].isin(cat)
    & df["content_format"].isin(fmt)
]

if f.empty:
    st.warning("No data for these filters. Select more options on the left.")
    st.stop()

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total interactions", f"{len(f):,}")
c2.metric("Unique users", f"{f['audience_id'].nunique():,}")
c3.metric("Posts engaged", f"{f['post_id'].nunique():,}")
c4.metric("Top category", f["content_category"].value_counts().idxmax())

st.divider()

# ---------- Charts ----------
left, right = st.columns(2)
with left:
    st.subheader("Interactions by content category")
    st.bar_chart(f["content_category"].value_counts())
with right:
    st.subheader("Interactions by content format")
    st.bar_chart(f["content_format"].value_counts())

left, right = st.columns(2)
with left:
    st.subheader("Interactions by action type")
    st.bar_chart(f["action_type"].value_counts())
with right:
    st.subheader("Interactions by age group")
    st.bar_chart(f["age_group"].value_counts())

st.subheader("Monthly trend")
st.line_chart(f.groupby("month").size())

st.subheader("Age group vs content category (number of interactions)")
pivot = pd.crosstab(f["age_group"], f["content_category"])
st.dataframe(pivot.style.background_gradient(cmap="Blues"), use_container_width=True)

st.subheader("Followers vs non-followers: action mix (%)")
mix = pd.crosstab(f["follower_status"], f["action_type"], normalize="index") * 100
st.dataframe(mix.round(1), use_container_width=True)

# ---------- Raw data ----------
with st.expander("See the joined data"):
    st.dataframe(f.drop(columns=["month"]).head(1000), use_container_width=True)
