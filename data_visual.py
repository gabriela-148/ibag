import streamlit as st
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Map full state names (as in your CSV) to USPS two-letter codes
state_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT",
    "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
}

REQUIRED_COLUMNS = ["Date", "State", "Value", "Measure"]

@st.cache_data
def load_data(path, measure, date_range=None):
    """Load CSV, validate, filter by measure—and optional date_range tuple."""
    # 1) Read + parse Date
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except pd.errors.EmptyDataError:
        st.error("Your CSV file is empty. Please upload a non-empty file.")
        st.stop()
    except pd.errors.ParserError as pe:
        st.error(f"Error parsing CSV: {pe}. Please check delimiters/quoting.")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error reading CSV: {e}")
        st.stop()

    # 2) Check required headers
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}. Required: {REQUIRED_COLUMNS}")
        st.stop()

    # 3) Filter by measure & drop bad rows
    df = df[df["Measure"] == measure].dropna(subset=["State", "Value"])
    if df.empty:
        st.warning(f"No data for Measure = '{measure}'.")
        st.stop()

    # 4) Create a date-only column
    df["Date_only"] = df["Date"].dt.date

    # 5) If user supplied a range, trim here
    if date_range is not None:
        start_date, end_date = date_range
        df = df[(df["Date_only"] >= start_date) & (df["Date_only"] <= end_date)]
        if df.empty:
            st.warning("No data in the selected date range.")
            st.stop()

    return df

@st.cache_data
def fit_model(df):
    encoder = OneHotEncoder(drop="first", sparse_output=False)
    X = encoder.fit_transform(df[["State"]])
    y = df["Value"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    lr = LinearRegression().fit(X_train, y_train)
    y_pred = lr.predict(X_test)
    return lr, encoder, y_test, y_pred

def get_coefficients(lr, encoder):
    names = encoder.get_feature_names_out(["State"])
    coefs = pd.DataFrame({"State": names, "Coefficient": lr.coef_})
    return coefs.sort_values("Coefficient", ascending=False)

def compare_models(df):
    """
    Fits LinearRegression and MLPRegressor on:
      - One-hot encoded 'State'
      - Numeric 'Date_ord' from your 'Date_only' column
    Returns a metrics DataFrame, the true y_test, and predictions dict.
    """
    # 1) Prepare numeric date feature
    df = df.copy()
    df["Date_ord"] = df["Date_only"].apply(lambda d: d.toordinal())

    # 2) One-hot encode State
    encoder = OneHotEncoder(drop="first", sparse_output=False)
    X_state = encoder.fit_transform(df[["State"]])

    # 3) Stack date + encoded state into feature matrix
    X = np.hstack([df[["Date_ord"]].values.reshape(-1, 1), X_state])
    y = df["Value"].values

    # 4) Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # 5) Define and fit both models
    models = {
        "Linear Regression": LinearRegression(),
        "MLP Regressor": MLPRegressor(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            solver="adam",
            max_iter=500,
            random_state=42
        )
    }

    results = []
    preds = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        preds[name] = y_pred

        results.append({
            "Model":  name,
            "R2":      r2_score(y_test, y_pred),
            "MSE":     mean_squared_error(y_test, y_pred)
        })

    metrics_df = pd.DataFrame(results).set_index("Model")
    return metrics_df, y_test, preds

def main():
    

    st.title("🛣️ Pedestrian Border Crossings Explorer")

    data_path = st.sidebar.file_uploader("Upload your CSV file", type="csv")
    measure   = st.sidebar.selectbox(
        "Select Measure",
        ["Pedestrians", "Trucks", "Personal Vehicles"]
    )


    if not data_path:
        st.info("Please upload your CSV to begin.")
        return

    # Load data (with Date_only)
    df_full = load_data(data_path, measure)

    # Sidebar date picker bounds
    min_date = df_full["Date_only"].min()
    max_date = df_full["Date_only"].max()

    # Date range input (returns Python date objects)
    start_date, end_date = st.sidebar.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # ---- Key fix: filter on Date_only rather than the datetime64 column ----
    df = df_full[
        (df_full["Date_only"] >= start_date) &
        (df_full["Date_only"] <= end_date)
    ]

    if df.empty:
        st.warning("No data available for this date range.")
        return

    # 2) Fit a simple linear model on the filtered data
    #    (reuse your fit_model function)
    lr_choice, encoder_choice, y_test_choice, y_pred_choice = fit_model(df_full)

    # 3) Build a DataFrame for plotting
    df_scatter = pd.DataFrame({
        "Actual":    y_test_choice,
        "Predicted": y_pred_choice
    })

        # —— New Choropleth Map Section ——
    # 1) Sum total crossings by State
    df_map = (
        df
        .groupby("State", as_index=False)["Value"]
        .sum()
        .rename(columns={"Value": "TotalCrossings"})
    )

    # 2) Map State names to USPS codes
    df_map["abbr"] = df_map["State"].map(state_abbrev)

    # 3) Build the Plotly choropleth
    fig_map = px.choropleth(
        df_map,
        locations="abbr",
        locationmode="USA-states",
        color="TotalCrossings",
        scope="usa",
        hover_name="State",
        color_continuous_scale="Viridis",
        labels={"TotalCrossings": "Total Pedestrian Crossings"},
        title=f"Total Crossings by State ({start_date} → {end_date})"
    )

    # 4) Render in Streamlit
    st.plotly_chart(fig_map, use_container_width=True)
    # —— End Choropleth Section ——

    # If no rows after filtering, bail out early
    if df.empty:
        st.warning("No data available for this date range.")
        return

    # Fit model and prepare charts on filtered df
    lr, encoder, y_test, y_pred = fit_model(df)
    coefs_sorted = get_coefficients(lr, encoder)

    # Display R²
    st.metric("R² Score", round(r2_score(y_test, y_pred), 3))

    start_fmt = start_date.strftime("%b %d, %Y")
    end_fmt   = end_date.strftime("%b %d, %Y")


    # Top 10 coefficients bar chart
    top10 = coefs_sorted.head(10)
    fig_bar = px.bar(
        top10, x="State", y="Coefficient",
        title=f"Top 10 States (from {start_fmt} to {end_fmt})",
        labels={"Coefficient": "Impact on Crossings"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    fig_scatter = px.scatter(
        x=y_test,
        y=y_pred,
        labels={"x": "Actual Value", "y": "Predicted Value"},
        title="Predicted vs. Actual Pedestrian Crossings"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Optional raw data preview
    if st.checkbox("Show raw data preview"):
        st.dataframe(df.head(50))

if __name__ == "__main__":
    main()
