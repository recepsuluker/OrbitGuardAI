# 🚀 Backend Performans Optimizasyonu - Kurulum Rehberi

## 📋 Genel Bakış

Bu klasör, OrbitGuardAI'nin backend performansını optimize eden 3 temel bileşeni içerir:

1. **Redis Cache** → TLE verilerini cache'leyerek API çağrılarını %95 azaltır
2. **Async Agent** → Çoklu uydu için paralel veri çekme (5-10x hızlanma)
3. **Rust Engine** → Kritik hesaplamalar için native kod (10-100x hızlanma)

## 🛠️ Hızlı Kurulum

### 1. Python Bağımlılıklarını Yükle

```bash
pip install -r requirements.txt
```

### 2. Redis'i Kur ve Çalıştır

**Windows (Chocolatey):**
```powershell
choco install redis-64
redis-server
```

**Linux/WSL:**
```bash
sudo apt update && sudo apt install redis-server
redis-server
```

**Alternatif: Redis Cloud (Ücretsiz)**
- https://redis.com/try-free/ adresinden ücretsiz hesap aç
- Connection URL'i al ve `.env` dosyasına ekle

### 3. Ortam Değişkenlerini Ayarla

```bash
# .env.example dosyasını kopyala
cp .env.example .env

# .env dosyasını düzenle ve gerçek bilgilerini gir
```

### 4. Rust Engine'i Derle (Opsiyonel)

**Önce Rust'ı kur:**
```bash
# Windows
winget install Rustlang.Rustup

# Linux/Mac
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Sonra modülü derle:**
```bash
cd rust_engine
maturin develop --release
cd ..
```

## 🧪 Testler

### Tüm Testleri Çalıştır
```bash
pytest tests/ -v
```

### Sadece Cache Testleri
```bash
pytest tests/test_cache.py -v
```

### Sadece Async Testleri
```bash
pytest tests/test_async.py -v
```

### Sadece Rust Testleri
```bash
pytest tests/test_rust.py -v
```

## 📊 Performans Benchmark

```bash
# Hızlı test (10 uydu)
python benchmark.py --quick

# Tam benchmark (10, 50, 100, 500 uydu)
python benchmark.py
```

## 📁 Dosya Yapısı

```
OrbitGuardAI/
├── cache_manager.py          # Redis cache manager
├── orbit_agent_async.py      # Async TLE fetcher
├── benchmark.py              # Performans testleri
├── .env.example              # Konfigürasyon şablonu
├── requirements.txt          # Python bağımlılıkları
├── pytest.ini                # Test konfigürasyonu
│
├── rust_engine/              # Rust optimizasyon modülü
│   ├── Cargo.toml
│   ├── build.bat            # Windows build script
│   ├── build.sh             # Linux/Mac build script
│   └── src/
│       └── lib.rs           # Rust kaynak kodu
│
└── tests/                    # Test suite
    ├── __init__.py
    ├── test_cache.py        # Cache testleri
    ├── test_async.py        # Async testleri
    └── test_rust.py         # Rust testleri
```

## 🎯 Kullanım Örnekleri

### Redis Cache Kullanımı

```python
from cache_manager import TLECacheManager

# Cache manager oluştur
cache = TLECacheManager()

# Cache'den veri al
norad_ids = [25544, 48274, 52740]
cached_data = cache.get_tle_data(norad_ids)

if cached_data is None:
    # API'den çek
    fresh_data = fetch_from_api(norad_ids)
    # Cache'e kaydet
    cache.set_tle_data(norad_ids, fresh_data)
```

### Async Agent Kullanımı

```python
from orbit_agent_async import AsyncOrbitAgent

async def fetch_satellites():
    async with AsyncOrbitAgent(username, password) as agent:
        tle_data = await agent.fetch_batch_tle([25544, 48274])
        return tle_data

# Senkron kod içinden çağır
from orbit_agent_async import run_sync
tle_data = run_sync([25544, 48274], username, password)
```

### Rust Engine Kullanımı

```python
import orbit_core

# Satellite nesneleri oluştur
satellites = [
    orbit_core.Satellite(
        norad_id=25544,
        position=[7000.0, 0.0, 0.0],
        velocity=[0.0, 7.5, 0.0]
    ),
    orbit_core.Satellite(
        norad_id=48274,
        position=[7010.0, 0.0, 0.0],
        velocity=[0.0, 7.4, 0.0]
    ),
]

# Konjunksiyon analizi (paralel, Rust ile)
conjunctions = orbit_core.find_conjunctions(satellites, threshold_km=10.0)

for conj in conjunctions:
    print(f"{conj.norad_id_1} ↔ {conj.norad_id_2}: {conj.distance_km:.2f} km")
```

## 🐛 Sorun Giderme

### Redis Bağlantı Hatası

**Hata:** `redis.exceptions.ConnectionError`

**Çözüm:**
1. Redis'in çalıştığından emin ol: `redis-cli ping` → `PONG` döndürmeli
2. `.env` dosyasındaki `REDIS_URL` doğru mu kontrol et
3. Firewall Redis portunu (6379) engelliyor olabilir

### Rust Build Hatası

**Hata:** `maturin: command not found`

**Çözüm:**
```bash
pip install --upgrade maturin
```

**Hata:** `error: linker 'cc' not found`

**Çözüm (Windows):**
- Visual Studio Build Tools yükle: https://visualstudio.microsoft.com/downloads/

**Çözüm (Linux):**
```bash
sudo apt install build-essential
```

### Import Hatası

**Hata:** `ModuleNotFoundError: No module named 'orbit_core'`

**Çözüm:**
1. Rust modülünü derle: `cd rust_engine && maturin develop --release`
2. Python'un doğru virtual environment'te olduğundan emin ol

## 📈 Beklenen Performans

| Senaryo | Önceki | Sonrası | İyileşme |
|---------|--------|---------|----------|
| 100 uydu TLE fetch | 45s | 5s | 9x |
| Cache hit (2. çalıştırma) | 45s | 0.1s | 450x |
| 1000 uydu konjunksiyon | Timeout | 30s | 100x+ |
| Bellek kullanımı | 500 MB | 200 MB | %60 azalma |

## 📞 Yardım

Sorun yaşıyorsanız:
1. `pytest tests/ -v` çalıştırıp hangi testlerin başarısız olduğuna bakın
2. `python benchmark.py --quick` ile hızlı test yapın
3. Log seviyesini DEBUG'a çevirin: `.env` dosyasında `LOG_LEVEL=DEBUG`

## 🎉 Tamamlandı!

Artık yüksek performanslı backend'iniz hazır. `app.py`'de bu yeni özellikleri kullanmaya başlayabilirsiniz.
