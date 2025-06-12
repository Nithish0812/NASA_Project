import streamlit as st
import pandas as pd
import pymysql
from datetime import date

# --- DB CONNECTION --
connection =  pymysql.connect(
        host='localhost',
        user='root',
        password='Nithish@9791',
        database='nasadb'
    )
cursor = connection.cursor()


# --- PAGE SETUP ---
st.set_page_config(page_title="NASA Asteroid Tracker", page_icon="🚀", layout="wide")
st.title("🚀 NASA Asteroid Tracker")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=120)
    tab = st.radio("Select View", ["Filter Criteria", "Queries"])

# --- FILTER PANEL ---
if tab == "Filter Criteria":
    st.subheader("🧪 Filter Criteria")

    col1, col2, col3 = st.columns(3)

    with col1:
        mag = st.slider("Absolute Magnitude (H)", 10.0, 35.0, (13.0, 30.0))
        dia_min = st.slider("Min Diameter (km)", 0.0, 5.0, (0.0, 3.0))
        dia_max = st.slider("Max Diameter (km)", 0.0, 12.0, (0.0, 10.0))

    with col2:
        velocity = st.slider("Relative Velocity (km/h)", 0.0, 200000.0, (1000.0, 150000.0))
        au = st.slider("Astronomical Unit (AU)", 0.0, 1.0, (0.0, 0.5))
        hazard = st.selectbox("Potentially Hazardous", ["All", "0", "1"])

    with col3:
        start_date = st.date_input("Start Date", date(2024, 1, 1))
        end_date = st.date_input("End Date", date(2025, 6, 30))

    if start_date > end_date:
        st.warning("Start date must be before end date.")
    elif st.button("🔎 Filter"):
        query = f"""
        SELECT ca.neo_reference_id, ca.close_approach_date, ca.relative_velocity_kmph,
               ca.astronomical_AU, ca.miss_distance_km, ca.orbiting_body, ca.miss_distance_lunar,
               a.name as asteroid_name, a.absolute_magnitude_h, a.estimated_diameter_min, a.estimated_diameter_max,
               a.is_potentially_hazardous_asteroid
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.close_approach_date BETWEEN %s AND %s
          AND a.absolute_magnitude_h BETWEEN %s AND %s
          AND a.estimated_diameter_min BETWEEN %s AND %s
          AND a.estimated_diameter_max BETWEEN %s AND %s
          AND ca.relative_velocity_kmph BETWEEN %s AND %s
          AND ca.astronomical_AU BETWEEN %s AND %s
        """

        params = [
            start_date,end_date,
            mag[0],mag[1],
            dia_min[0],dia_min[1],
            dia_max[0],dia_max[1],
            velocity[0],velocity[1],
            au[0],au[1]]
        
        if hazard != "All":
            query += f" AND a.is_potentially_hazardous_asteroid = %s"
            params.append(int(hazard))

        cursor.execute(query, params)
        result = cursor.fetchall()
        df = pd.DataFrame(
            result,columns=[i[0] for i in cursor.description])
        st.subheader("📋 Filtered Results")
        st.caption(f"Total Records: {len(df)}")
        st.dataframe(df, use_container_width=1)

# --- QUERY PANEL ---
elif tab == "Queries":
    st.subheader("📦 Predefined Queries")

    query_options = {
        "1. Count how many times each asteroid has approached Earth": 
        """
        SELECT a.name, COUNT(*) AS approach_count
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.name
        ORDER BY approach_count DESC;
        """,

        "2. Average velocity of each asteroid over multiple approaches": 
        """
        SELECT a.name, ROUND(AVG(ca.relative_velocity_kmph), 2) AS avg_velocity
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.name
        ORDER BY avg_velocity DESC;
        """,

        "3. List top 10 fastest asteroids":
        """
        SELECT a.name, MAX(ca.relative_velocity_kmph) AS max_velocity
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        GROUP BY a.name
        ORDER BY max_velocity DESC
        LIMIT 10;
        """,

        "4. Potentially hazardous asteroids (more than 3 approaches)": 
        """
        SELECT a.name, COUNT(*) AS approach_count
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE a.is_potentially_hazardous_asteroid = 1
        GROUP BY a.name
        HAVING COUNT(*) > 3
        ORDER BY approach_count DESC;
        """,

        "5. Month with the most asteroid approaches": 
        """
        SELECT DATE_FORMAT(close_approach_date, '%Y-%m') AS month, COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY month
        ORDER BY approach_count DESC
        LIMIT 1;
        """,
        
        "6. Asteroid with the fastest ever approach speed": 
        """
        SELECT a.name, ca.relative_velocity_kmph, ca.close_approach_date
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        ORDER BY ca.relative_velocity_kmph DESC
        LIMIT 1;
        """,

        "7. Sort asteroids by max estimated diameter (descending)": 
        """
        SELECT name, estimated_diameter_max
        FROM asteroids
        ORDER BY estimated_diameter_max DESC;
        """,
    
        "8. Asteroid whose closest approach is getting nearer": 
        """
        SELECT ca.neo_reference_id, a.name, ca.close_approach_date, ca.miss_distance_km
        FROM close_approach ca
        JOIN (
            SELECT neo_reference_id
            FROM close_approach
            GROUP BY neo_reference_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
        ) most_approaches ON ca.neo_reference_id = most_approaches.neo_reference_id
        JOIN asteroids a ON a.id = ca.neo_reference_id
        ORDER BY ca.close_approach_date ASC;
        """,

        "9. Each asteroid's closest approach (date and distance)": 
        """
        SELECT a.name, ca.close_approach_date, ca.miss_distance_km
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE (ca.neo_reference_id, ca.miss_distance_km) IN (
            SELECT neo_reference_id, MIN(miss_distance_km)
            FROM close_approach
            GROUP BY neo_reference_id
        );
        """,
        "10. Asteroids with velocity > 50,000 km/h":
        """
        SELECT DISTINCT a.name, ca.relative_velocity_kmph, ca.close_approach_date
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.relative_velocity_kmph > 50000
        ORDER BY ca.relative_velocity_kmph DESC;
        """,

        "11. Count how many approaches happened per month": 
        """
        SELECT DATE_FORMAT(close_approach_date, '%Y-%m') AS month, COUNT(*) AS total_approaches
        FROM close_approach
        GROUP BY month
        ORDER BY month;
        """,

        "12. Asteroid with the highest brightness (lowest magnitude)": 
        """
        SELECT name, absolute_magnitude_h
        FROM asteroids
        ORDER BY absolute_magnitude_h ASC
        LIMIT 1;
        """,

        "13. Hazardous vs Non-hazardous asteroids count": 
        """
        SELECT 
          CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 'Hazardous' ELSE 'Non-Hazardous' END AS type,
          COUNT(*) AS count
        FROM asteroids
        GROUP BY is_potentially_hazardous_asteroid;
        """,

        "14. Asteroids that passed closer than the Moon (< 1 LD)":
        """
        SELECT a.name, ca.close_approach_date, ca.miss_distance_lunar
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.miss_distance_lunar < 1
        ORDER BY ca.miss_distance_lunar ASC;
        """,

        "15. Asteroids that came within 0.05 AU":
        """
        SELECT a.name, ca.close_approach_date, ca.astronomical_AU
        FROM close_approach ca
        JOIN asteroids a ON ca.neo_reference_id = a.id
        WHERE ca.astronomical_AU < 0.05
        ORDER BY ca.astronomical_AU ASC;
        """   

    }

    selected = st.selectbox("Choose a query", list(query_options.keys()))

    if selected:
        st.code(query_options[selected], language='sql')
        cursor.execute(query_options[selected])
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] 
    for i in cursor.description])
        st.dataframe(df, use_container_width=1)

