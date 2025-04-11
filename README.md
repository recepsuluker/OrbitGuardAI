
# 🛰️ OrbitGuard AI

OrbitGuard AI is a smart satellite tracking and monitoring agent that:
- Connects to [Space-Track.org](https://www.space-track.org) for real-time TLE data
- Performs proximity analysis between satellites (conjunction detection)
- Calculates satellite visibility based on base station location
- Generates both **2D** (Folium) and **3D** (Plotly) Earth visualizations
- Exports results as downloadable **CSV** and **HTML** files

---

## 🚀 Features

✅ Automatic TLE retrieval from Space-Track  
✅ Satellite-to-satellite conjunction warnings  
✅ Base station visibility pass predictions  
✅ Interactive 2D & 3D world maps  
✅ CSV/HTML export for post-analysis  
✅ Streamlit UI for easy interaction

---

## 📸 Demo

![OrbitGuard AI Interface](docs/screenshot.png)

---

## 🧰 Requirements

Install dependencies from the provided file:

```bash
pip install -r requirements.txt
```

---

## 🖥️ How to Run

Launch the Streamlit web UI:

```bash
streamlit run app.py
```

---

## 🧠 Usage

1. Enter your Space-Track credentials (free registration required)
2. Input at least 5 NORAD IDs (e.g., `52739,55012,56210,58256,58268`)
3. Set your **base station** location (lat/lon/elevation)
4. Click `🚀 Run Full Analysis`
5. View 2D/3D satellite maps and download CSV reports

---

## 📁 Output Files

- `outputs/conjunction-warning.csv` → Close encounter report  
- `outputs/plan_s_satellite_passes.csv` → Visibility from your ground station  
- `outputs/satellite_track_2d.html` → 2D Folium map  
- `outputs/satellite_track_3d.html` → 3D Plotly globe

---

## 📦 Project Structure

```
OrbitGuardAI/
├── app.py                   # Streamlit interface
├── orbit_agent.py           # Core AI agent logic
├── requirements.txt         # Python dependencies
├── outputs/                 # Exported results
```

---

## 👨‍💻 Credits

Developed by [Your Name] – inspired by Plan-S satellite data tracking and real-time LEO traffic analysis.

---

## 📄 License

MIT License – free for commercial and personal use.
