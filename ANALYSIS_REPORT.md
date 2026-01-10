# 🛰️ OrbitGuard AI - Proje Analizi ve Öneriler Raporu

**Tarih:** 10 Ocak 2026  
**Analiz Yapan:** Antigravity AI  

---

## 📋 İçindekiler

1. [Proje Özeti](#proje-özeti)
2. [Tespit Edilen Sorunlar](#tespit-edilen-sorunlar)
3. [Çalışmayan Özellikler](#çalışmayan-özellikler)
4. [Geliştirme Önerileri](#geliştirme-önerileri)
5. [Teknik İyileştirmeler](#teknik-iyileştirmeler)
6. [Yeni Özellik Önerileri](#yeni-özellik-önerileri)

---

## 🔍 Proje Özeti

OrbitGuard AI, LEO (Low Earth Orbit) uydularını izleyen ve çarpışma risk analizi yapan bir uydu takip sistemidir:

| Özellik | Durum |
|---------|-------|
| Space-Track.org TLE Verisi | ✅ Çalışıyor |
| Celestrak Fallback | ✅ Çalışıyor |
| 2D Harita (Folium) | ✅ Çalışıyor |
| 3D Globe (Pydeck) | ⚠️ Kısmen Çalışıyor |
| Conjunction Analysis (SGP4) | ✅ Çalışıyor |
| Scientific Mode (Keplerian) | ⚠️ Kısmen Çalışıyor |
| Email Alerts | ❌ Çalışmıyor |
| J2 Perturbation Model | ⚠️ Kısmen Çalışıyor |

---

## 🚨 Tespit Edilen Sorunlar

### 1. **`orbit_engine.py` - Incomplete `calculate_conjunction_nodes` Fonksiyonu**

**Sorun:** İlk `calculate_conjunction_nodes` fonksiyonu (satır 85-130) yarım bırakılmış ve return statement yok. Aynı isimde ikinci bir fonksiyon (satır 160-238) tanımlanmış.

```python
# Satır 85-130: İlk fonksiyon tanımı (eksik)
def calculate_conjunction_nodes(self, sat1, sat2, t):
    # ... code ...
    # ❌ RETURN STATEMENT YOK! Fonksiyon yarım bırakılmış.
    
def get_perifocal_rotation_matrix(self, ...):  # Satır 131
    # ...
    
def calculate_conjunction_nodes(self, sat1, sat2, t):  # Satır 160 - İkinci tanım
    # Bu çalışıyor ama ilk tanım Python'da override ediliyor
```

**Çözüm:** İlk fonksiyon tanımını tamamen silmek gerekiyor (satır 85-130).

---

### 2. **Email Alerts Özelliği Gerçek Bir Fonksiyonelliğe Sahip Değil**

**Dosya:** `app.py` (satır 323-333)

**Sorun:** Email subscription sadece bir success mesajı gösteriyor, gerçekte email göndermiyor.

```python
if st.button("Subscribe to Alerts"):
    if email_input and "@" in email_input:
        st.success(f"Subscribed! Alerts for risks > {alert_threshold}% will be sent to {email_input}.")
        # ❌ Gerçek email gönderimi yok!
```

**Çözüm:** SMTP entegrasyonu veya bir email servisi (SendGrid, Mailgun) kullanarak gerçek notification sistemi implement edilmeli.

---

### 3. **Exception Handling Eksiklikleri**

**Dosya:** `orbit_agent.py` (satır 28, 74, 119)

**Sorun:** Bare `except` kullanımı hataları yutabiliyor.

```python
except:  # ❌ Hangi hata olduğu belli değil
    pass
```

**Çözüm:** Spesifik exception tipler

i kullanılmalı:

```python
except requests.RequestException as e:
    print(f"Request failed: {e}")
```

---

### 4. **`requirements.txt` Eksik Bağımlılıklar**

**Mevcut:**
```
skyfield, pandas, numpy, plotly, folium, requests, streamlit, pydeck
```

**Eksik:**
- Versiyon numaraları yok (compatibility sorunlarına yol açabilir)
- `scipy` (bazı hesaplamalar için gerekebilir)

---

### 5. **3D Globe Visualization - Performans Sorunları**

**Dosya:** `visualization.py` (satır 143-276)

**Sorun:** 
- Orbit path hesaplamak için Skyfield propagation yapılıyor (yavaş)
- 2000+ uydu için performans düşüyor
- Mapbox API key gereksinimi yorum satırına alınmış ama globe render düzgün olmayabilir

---

### 6. **J2 Propagator Kepler Denklemi Çözümü Yetersiz**

**Dosya:** `orbit_engine.py` (satır 430-434)

```python
E_new = M_new
for _ in range(5):  # ❌ Sadece 5 iterasyon yeterli olmayabilir
    E_new = M_new + e * np.sin(E_new)
```

**Çözüm:** Yakınsama kontrolü eklemeli:

```python
for _ in range(50):
    E_prev = E_new
    E_new = M_new + e * np.sin(E_new)
    if abs(E_new - E_prev) < 1e-10:
        break
```

---

## ❌ Çalışmayan Özellikler

| Özellik | Sorun | Kritiklik |
|---------|-------|-----------|
| **Email Alerts** | Sadece UI var, backend yok | 🔴 Yüksek |
| **Full Catalog Analysis** | 5000 limit var, gerçek 20000+ için test edilmemiş | 🟡 Orta |
| **Risk Timeline** | J2 propagator hassasiyet sorunu | 🟡 Orta |
| **CSV Export (some modes)** | Scientific mode'da CSV export yok | 🟡 Orta |

---

## 💡 Geliştirme Önerileri

### Kısa Vadeli (Hızlı Kazanımlar)

#### 1. **Kod Temizliği - Duplicate Fonksiyon Silme**
```diff
# orbit_engine.py satır 85-130 silinmeli
- def calculate_conjunction_nodes(self, sat1, sat2, t):
-     """İlk eksik tanım..."""
-     el1 = sat1.calculate_elements(t)
-     ... (50 satır eksik kod)
```

#### 2. **Error Handling İyileştirme**
```python
# Önceki
except:
    pass

# Sonrası  
except requests.exceptions.Timeout as e:
    logging.warning(f"Request timeout: {e}")
except requests.exceptions.RequestException as e:
    logging.error(f"Request failed: {e}")
```

#### 3. **Requirements.txt Versiyonlama**
```
skyfield>=1.45
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
folium>=0.14.0
requests>=2.28.0
streamlit>=1.28.0
pydeck>=0.8.0
```

---

### Orta Vadeli (1-2 Hafta)

#### 4. **Gerçek Email Notification Sistemi**

```python
import smtplib
from email.mime.text import MIMEText
import os

class AlertSystem:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("ALERT_EMAIL")
        self.sender_password = os.getenv("ALERT_PASSWORD")
    
    def send_alert(self, recipient, subject, body):
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient, msg.as_string())
```

#### 5. **Database Entegrasyonu (SQLite/PostgreSQL)**

Uydu verilerini ve alert subscriptions'ları kaydetmek için:

```python
# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AlertSubscription(Base):
    __tablename__ = 'alert_subscriptions'
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    threshold_percent = Column(Float)
    satellite_ids = Column(String(1000))  # JSON
    created_at = Column(DateTime)

class ConjunctionEvent(Base):
    __tablename__ = 'conjunction_events'
    id = Column(Integer, primary_key=True)
    sat1_name = Column(String(100))
    sat2_name = Column(String(100))
    distance_km = Column(Float)
    event_time = Column(DateTime)
    probability = Column(Float)
```

#### 6. **Scientific Mode CSV Export**

```python
# app.py Scientific Mode bölümüne eklenecek
if st.button("📥 Export Scientific Results"):
    import io
    
    # Satellites criticality export
    sat_data = [{
        'name': s.name,
        'norad_id': s.norad_id,
        'criticality_score': s.criticality_score,
        'orbital_elements': str(s.orbital_elements)
    } for s in sci_sats]
    
    df_sats = pd.DataFrame(sat_data)
    csv_sats = df_sats.to_csv(index=False)
    
    st.download_button(
        label="Download Satellite Criticality CSV",
        data=csv_sats,
        file_name="satellite_criticality.csv",
        mime="text/csv"
    )
    
    # Nodes export
    if all_nodes:
        df_nodes = pd.DataFrame(all_nodes)
        csv_nodes = df_nodes.to_csv(index=False)
        st.download_button(
            label="Download Conjunction Nodes CSV",
            data=csv_nodes,
            file_name="conjunction_nodes.csv",
            mime="text/csv"
        )
```

---

### Uzun Vadeli (Yeni Özellikler)

#### 7. **Collision Probability Hesaplama (Pc)**

Şu anki sistem sadece mesafe bazlı. Gerçek collision probability hesaplama eklenmeli:

```python
class CollisionProbabilityCalculator:
    """
    Monte Carlo veya Alfano method ile Pc hesaplama.
    """
    def calculate_pc_alfano(self, miss_distance, combined_covariance):
        # Alfano 2005 method
        pass
    
    def calculate_pc_monte_carlo(self, sat1_state, sat2_state, covariance1, covariance2, n_samples=10000):
        # Monte Carlo simulation
        pass
```

#### 8. **Maneuver Planning Modülü**

Çarpışma riski yüksek uydular için manevra önerisi:

```python
class ManeuverPlanner:
    def suggest_avoidance_maneuver(self, satellite, conjunction_event):
        """
        Delta-V hesaplayarak çarpışmadan kaçınma manevrası önerir.
        """
        # Hohmann transfer veya impulsive maneuver hesabı
        pass
```

#### 9. **Real-time Tracking WebSocket**

```python
# websocket_server.py
import asyncio
import websockets
import json

async def satellite_tracker(websocket, path):
    while True:
        positions = get_current_positions()  # TLE'den hesapla
        await websocket.send(json.dumps(positions))
        await asyncio.sleep(1)  # Her saniye güncelle
```

#### 10. **Machine Learning Risk Prediction**

```python
from sklearn.ensemble import RandomForestClassifier

class MLRiskPredictor:
    def __init__(self):
        self.model = RandomForestClassifier()
    
    def train(self, historical_conjunctions):
        # Geçmiş conjunction olaylarından öğren
        pass
    
    def predict_risk(self, sat1, sat2, time_horizon_days=7):
        # ML ile risk tahmini
        pass
```

---

## 🔧 Teknik İyileştirmeler

### 1. **Logging Sistemi**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orbitguard.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('OrbitGuardAI')
```

### 2. **Configuration Management**

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    space_track_username: str = ""
    space_track_password: str = ""
    default_threshold_km: float = 10.0
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    class Config:
        env_file = ".env"
```

### 3. **Unit Tests Ekleme**

```python
# tests/test_orbit_engine.py
import pytest
from orbit_engine import KeplerianEngine, ScientificSatellite

class TestKeplerianEngine:
    def test_apogee_perigee_filter(self):
        engine = KeplerianEngine(tolerance_km=10.0)
        # Test implementation
        
    def test_conjunction_nodes_calculation(self):
        # Test with known values
        pass
```

### 4. **Docker Desteği**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  orbitguard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SPACE_TRACK_USERNAME=${SPACE_TRACK_USERNAME}
      - SPACE_TRACK_PASSWORD=${SPACE_TRACK_PASSWORD}
    volumes:
      - ./outputs:/app/outputs
```

---

## 📊 Öncelik Matrisi

| Öneri | Etki | Çaba | Öncelik |
|-------|------|------|---------|
| Duplicate fonksiyon silme | Yüksek | Düşük | 🔴 P1 |
| Error handling düzeltme | Orta | Düşük | 🔴 P1 |
| Requirements versiyonlama | Orta | Düşük | 🔴 P1 |
| J2 propagator fix | Yüksek | Orta | 🟡 P2 |
| Email notification | Yüksek | Orta | 🟡 P2 |
| Scientific CSV export | Orta | Düşük | 🟡 P2 |
| Database entegrasyonu | Orta | Yüksek | 🟢 P3 |
| Collision Probability | Yüksek | Yüksek | 🟢 P3 |
| ML Risk Prediction | Yüksek | Çok Yüksek | 🔵 P4 |

---

## 🎯 Sonuç

OrbitGuard AI, sağlam bir temel üzerine kurulmuş kapsamlı bir uydu takip sistemidir. Yukarıdaki sorunlar giderildiğinde ve önerilen özellikler eklendiğinde, profesyonel seviyede kullanılabilir bir araç olacaktır.

**Acil Yapılması Gerekenler:**
1. ✅ `orbit_engine.py` duplicate fonksiyon temizliği
2. ✅ Exception handling iyileştirmeleri
3. ✅ Requirements.txt versiyonlama

**Kısa Vadeli Hedefler:**
1. 📧 Email notification sistemi
2. 📊 Scientific mode CSV export
3. 🔧 J2 propagator hassasiyet artırımı

---

*Bu rapor OrbitGuard AI projesinin kapsamlı kod incelemesine dayanılarak hazırlanmıştır.*


https://nadir.space/trackers/live-satellite-map

3D Harita Toggle bu sekilide olsun lutfen ilgili kutuphaleri indir ve guncelle 

🔐 Space-Track Credentials kullanici adi ve sifre gordikten sonra "log in" butonu ekle cunku bu sekilide kullanici giris yaptiginda emin olsun. 

Dark Tema icinde renk uyumunu begenmedim daha futuruictik bir renk uyumu kullan. 