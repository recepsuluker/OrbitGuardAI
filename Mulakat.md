# 🛰️ OrbitGuard AI - Mülakat Özeti
## Interview Summary

---

# 🇹🇷 TÜRKÇE

## Proje Adı
**OrbitGuard AI: Scientific LEO Risk Suite**

## Özet
OrbitGuard AI, Düşük Dünya Yörüngesindeki (LEO) uyduların çarpışma risklerini analiz eden, bilimsel temelli bir yapay zeka destekli izleme sistemidir. Sistem, gerçek zamanlı uydu takibi, kavşak noktası (conjunction node) hesaplama ve risk tahmini yapabilmektedir.

---

## 🎯 Problem
- Uzay çöpü ve uydu kalabalığı her geçen gün artmaktadır
- LEO'da 20.000+ aktif nesne bulunmaktadır
- Çarpışma riski hesaplama karmaşık ve kaynak yoğun bir işlemdir
- Operatörlerin hızlı karar vermesi için gerçek zamanlı analize ihtiyaç vardır

---

## 💡 Çözüm
OrbitGuard AI iki modda çalışan entegre bir analiz sistemi sunar:

### 1. Operasyonel Mod (SGP4)
- **Gerçek zamanlı uydu takibi** - Space-Track ve Celestrak API'lerinden TLE verisi çekme
- **Yakın geçiş analizi** - SGP4 propagasyon ile mesafe hesaplama
- **Yer istasyonu görünürlüğü** - Belirlenen konumdan uydu geçişlerini takip
- **2D/3D görselleştirme** - Folium ve Pydeck ile interaktif haritalar

### 2. Bilimsel Mod (Keplerian)
- **Geometrik kavşak noktası hesaplama** - Yörünge düzlemlerinin kesişim doğrusu
- **Kritiklik skoru (f_sc)** - Her uydu için çarpışma risk değerlendirmesi
- **Nodal frekans (f_nc)** - Kavşak noktalarında buluşma sıklığı
- **Vektörize apogee/perigee filtresi** - O(N²) yerine optimize edilmiş arama

---

## 🔧 Teknik Detaylar

### Kullanılan Teknolojiler
| Kategori | Teknoloji |
|----------|-----------|
| **Backend** | Python 3.x |
| **Web Framework** | Streamlit |
| **Yörünge Mekaniği** | Skyfield, SGP4, Keplerian Elements |
| **Veri Kaynakları** | Space-Track.org, Celestrak |
| **Görselleştirme** | Plotly, Pydeck, Folium |
| **Pertürbasyon** | J2 Propagation Model |
| **Deployment** | Jetson Nano Developer Kit |
| **Tunnel/Proxy** | Cloudflare Tunnel |

### Mimari Yapı
```
OrbitGuardAI/
├── app.py              # Streamlit web arayüzü
├── orbit_agent.py      # TLE çekme, SGP4 analiz, harita oluşturma
├── orbit_engine.py     # Keplerian hesaplamalar, J2 propagasyon, risk analizi
└── visualization.py    # Pydeck 3D globe, Plotly grafikleri
```

### Temel Algoritmalar

#### 1. Kavşak Noktası Hesaplama
```
1. İki yörünge düzleminin normal vektörlerini hesapla (h₁, h₂)
2. Kesişim doğrusunu bul: L = h₁ × h₂
3. Her uydu için kesişim noktasındaki yarıçapı hesapla
4. |r₁ - r₂| < tolerans ise kavşak noktası var
```

#### 2. Kritiklik Skoru
```
f_sc = Σ f_nc  (tüm kavşak noktaları için)
f_nc = 30 / T_c  (aylık kavşak frekansı)
T_c = 2π / |n₁ - n₂|  (sinodik periyot)
```

#### 3. J2 Pertürbasyonu
- RAAN kayması: Ω̇ = -1.5 n J₂ (Re/p)² cos(i)
- Perihel kayması: ω̇ = -1.5 n J₂ (Re/p)² (2.5 sin²(i) - 2)

---

## 🚀 Öne Çıkan Özellikler

1. **Hibrit Analiz** - SGP4 operasyonel + Keplerian bilimsel mod
2. **Vektörize Filtreleme** - 20.000+ uydu için optimize edilmiş O(N log N) algoritma
3. **7 Günlük Tahmin** - J2 pertürbasyonu ile risk timeline
4. **Edge Deployment** - Jetson Nano üzerinde çalışabilir (düşük güç tüketimi)
5. **Gerçek Zamanlı Veri** - Space-Track ve Celestrak entegrasyonu

---

## 📊 Sonuçlar ve Metrikler
- 5000+ uydu için kavşak analizi yapabilme
- Saniyeler içinde kritiklik skoru hesaplama
- 7 gün ileri risk tahmini
- Düşük maliyet donanım üzerinde çalışma (Jetson Nano ~$99)

---

## 🔮 Gelecek Geliştirmeler
- Machine Learning ile risk sınıflandırma
- Manevra optimizasyonu önerisi
- Email/SMS uyarı sistemi
- Constellation yönetimi modülü

---
---

# 🇬🇧 ENGLISH

## Project Name
**OrbitGuard AI: Scientific LEO Risk Suite**

## Summary
OrbitGuard AI is a scientifically-grounded, AI-assisted monitoring system that analyzes collision risks for satellites in Low Earth Orbit (LEO). The system provides real-time satellite tracking, conjunction node calculation, and risk forecasting capabilities.

---

## 🎯 Problem
- Space debris and satellite congestion are increasing daily
- Over 20,000+ active objects in LEO
- Collision risk calculation is complex and resource-intensive
- Operators need real-time analysis for quick decision-making

---

## 💡 Solution
OrbitGuard AI provides an integrated analysis system operating in two modes:

### 1. Operational Mode (SGP4)
- **Real-time satellite tracking** - Fetching TLE data from Space-Track and Celestrak APIs
- **Close approach analysis** - Distance calculation using SGP4 propagation
- **Ground station visibility** - Tracking satellite passes from specified location
- **2D/3D visualization** - Interactive maps with Folium and Pydeck

### 2. Scientific Mode (Keplerian)
- **Geometric conjunction node calculation** - Line of intersection between orbital planes
- **Criticality score (f_sc)** - Collision risk assessment for each satellite
- **Nodal frequency (f_nc)** - Encounter frequency at conjunction nodes
- **Vectorized apogee/perigee filter** - Optimized search instead of O(N²)

---

## 🔧 Technical Details

### Technologies Used
| Category | Technology |
|----------|-----------|
| **Backend** | Python 3.x |
| **Web Framework** | Streamlit |
| **Orbital Mechanics** | Skyfield, SGP4, Keplerian Elements |
| **Data Sources** | Space-Track.org, Celestrak |
| **Visualization** | Plotly, Pydeck, Folium |
| **Perturbation** | J2 Propagation Model |
| **Deployment** | Jetson Nano Developer Kit |
| **Tunnel/Proxy** | Cloudflare Tunnel |

### Architecture
```
OrbitGuardAI/
├── app.py              # Streamlit web interface
├── orbit_agent.py      # TLE fetching, SGP4 analysis, map generation
├── orbit_engine.py     # Keplerian calculations, J2 propagation, risk analysis
└── visualization.py    # Pydeck 3D globe, Plotly charts
```

### Core Algorithms

#### 1. Conjunction Node Calculation
```
1. Calculate normal vectors for two orbital planes (h₁, h₂)
2. Find intersection line: L = h₁ × h₂
3. Calculate radius at intersection point for each satellite
4. If |r₁ - r₂| < tolerance, conjunction node exists
```

#### 2. Criticality Score
```
f_sc = Σ f_nc  (for all conjunction nodes)
f_nc = 30 / T_c  (monthly conjunction frequency)
T_c = 2π / |n₁ - n₂|  (synodic period)
```

#### 3. J2 Perturbation
- RAAN drift: Ω̇ = -1.5 n J₂ (Re/p)² cos(i)
- Perihelion drift: ω̇ = -1.5 n J₂ (Re/p)² (2.5 sin²(i) - 2)

---

## 🚀 Key Features

1. **Hybrid Analysis** - SGP4 operational + Keplerian scientific mode
2. **Vectorized Filtering** - Optimized O(N log N) algorithm for 20,000+ satellites
3. **7-Day Forecast** - Risk timeline with J2 perturbation
4. **Edge Deployment** - Runs on Jetson Nano (low power consumption)
5. **Real-time Data** - Space-Track and Celestrak integration

---

## 📊 Results and Metrics
- Conjunction analysis for 5000+ satellites
- Criticality score calculation in seconds
- 7-day forward risk forecasting
- Low-cost hardware deployment (Jetson Nano ~$99)

---

## 🔮 Future Improvements
- Machine Learning based risk classification
- Maneuver optimization suggestions
- Email/SMS alert system
- Constellation management module

---

## 🎤 Interview Talking Points

### "Tell me about your project"
> "I developed OrbitGuard AI, a satellite collision risk analysis system. It combines operational SGP4 tracking with scientific Keplerian analysis to identify high-risk satellites in LEO. The system calculates criticality scores based on nodal conjunction frequency and can forecast risks up to 7 days ahead using J2 perturbation modeling. I deployed it on a Jetson Nano edge device with Cloudflare Tunnel for global access."

### "What challenges did you face?"
> "The main challenge was optimizing the O(N²) pairwise comparison for 20,000+ satellites. I implemented a vectorized apogee/perigee filter that reduces candidate pairs significantly before running expensive geometric calculations. This brought the analysis time from hours to seconds."

### "Why is this important?"
> "With Starlink and other mega-constellations, LEO is becoming increasingly crowded. A single collision could create thousands of debris pieces, triggering a Kessler Syndrome cascade. OrbitGuard AI helps operators identify and prioritize high-risk scenarios before they become critical."

---

## 🔗 Live Demo
**https://monitor.aysegulsarisuluker.com/**

---

*Created for interview preparation - OrbitGuard AI Project*
