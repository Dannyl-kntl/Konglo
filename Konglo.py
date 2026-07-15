# ===== BOT SCAN SAHAM KONGLO (Konglomerasi) =====
# Jalankan setiap hari jam 15:30 WIB

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# --- 🔴 GANTI DENGAN TOKEN BARU KAMU ---
TOKEN = "8530677074:AAFATNDsDfbQ4HJ5dmW_-coeW69cgSzimiY"
CHAT_ID = "8995282419"  # atau ID grup
# -----------------------------------------

# DAFTAR SAHAM KONGLO (Update Juli 2026)
LIST_KONGLO = [
    'BREN.JK', 'DSSA.JK', 'SMAR.JK', 'MORA.JK',  # Sinar Mas
    'BELI.JK', 'BBCA.JK', 'TOWR.JK', 'MTEL.JK',  # Djarum
    'DNET.JK', 'INDF.JK', 'ICBP.JK', 'AMMN.JK',  # Salim
    'MLPT.JK',                                    # Lippo
    'BYAN.JK', 'DCII.JK', 'PGUN.JK', 'CMNP.JK',  # Konglo lainnya
    'ASII.JK',                                    # Astra
]

def kirim_pesan(pesan):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.get(url, params={'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}, timeout=10)
        if resp.status_code == 200:
            hasil = resp.json()
            if not hasil.get('ok'):
                print(f"❌ ERROR DARI TELEGRAM: {hasil.get('description')}")
            else:
                print("✅ Pesan berhasil terkirim!")
        else:
            print(f"❌ HTTP Error: {resp.status_code}")
    except Exception as e:
        print(f"❌ Gagal konek: {e}")

def analisis_konglo(kode):
    try:
        saham = yf.Ticker(kode)
        df = saham.history(period="120d")
        if df.empty or len(df) < 50:
            return None
        
        info = saham.info
        
        # Indikator Teknikal
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Volume & Free Float (estimasi dari market cap vs volume)
        avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-1]
        vol_hari_ini = last['Volume']
        volume_ratio = vol_hari_ini / avg_vol_20 if avg_vol_20 > 0 else 0
        
        harga = last['Close']
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # === KRITERIA KONGLO ===
        # 1. Harga di atas MA50 (tren jangka menengah naik)
        # 2. RSI sehat (40-70)
        # 3. Volume tidak terlalu liar (tanda konglo cenderung stabil)
        kondisi_konglo = (
            harga > last['MA50'] and
            40 < last['RSI'] < 70 and
            volume_ratio < 2.5  # Volume tidak melonjak liar
        )
        
        # Ambil informasi grup (hardcode)
        grup = "Unknown"
        if kode in ['BREN.JK', 'DSSA.JK', 'SMAR.JK', 'MORA.JK']:
            grup = "Sinar Mas"
        elif kode in ['BELI.JK', 'BBCA.JK', 'TOWR.JK', 'MTEL.JK']:
            grup = "Djarum"
        elif kode in ['DNET.JK', 'INDF.JK', 'ICBP.JK', 'AMMN.JK']:
            grup = "Salim"
        elif kode == 'MLPT.JK':
            grup = "Lippo"
        elif kode in ['BYAN.JK', 'DCII.JK']:
            grup = "Low Tuck Kwong / Otto"
        elif kode == 'ASII.JK':
            grup = "Astra"
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': info.get('shortName', kode)[:25],
            'grup': grup,
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last['RSI'], 2),
            'ma50': round(last['MA50'], 2),
            'volume_ratio': round(volume_ratio, 2),
            'is_konglo': kondisi_konglo,
            'atr': round(last['ATR'], 2),
        }
    except Exception as e:
        return None

# ===== MAIN =====
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"Scan Konglo dimulai: {waktu}")

hasil = []
for kode in LIST_KONGLO:
    res = analisis_konglo(kode)
    if res:
        hasil.append(res)

# === BUAT PESAN ===
pesan = f"🏛️ *SCAN SAHAM KONGLO - {waktu}*\n"
pesan += f"📌 Total: {len(hasil)} saham konglo\n"
pesan += "=" * 30 + "\n\n"

# Pisahkan yang sehat vs perlu diwaspadai
sehat = [h for h in hasil if h['is_konglo']]
waspada = [h for h in hasil if not h['is_konglo']]

if sehat:
    pesan += "✅ *SAHAM KONGLO SEHAT (TREN NAIK)*\n\n"
    for h in sehat[:5]:  # Tampilkan 5 teratas
        pesan += f"🏢 *{h['kode']}* - {h['grup']}\n"
        pesan += f"💰 Rp{h['harga']:.0f} | 📈 {h['perubahan']:+.2f}%\n"
        pesan += f"📊 RSI: {h['rsi']} | MA50: Rp{h['ma50']:.0f}\n"
        pesan += f"📦 Volume vs Rata2: {h['volume_ratio']}x\n"
        pesan += "-" * 20 + "\n"
else:
    pesan += "⏳ Belum ada saham konglo yang memenuhi kriteria tren naik.\n\n"

# Tambahkan yang perlu diwaspadai (RSI tinggi atau volume aneh)
if waspada:
    pesan += "⚠️ *PERHATIAN (RSI Tinggi / Volume Anomali)*\n\n"
    for h in sorted(waspada, key=lambda x: x['rsi'], reverse=True)[:3]:
        pesan += f"🔹 {h['kode']} | RSI: {h['rsi']} | Vol: {h['volume_ratio']}x\n"

kirim_pesan(pesan)
print("✅ Selesai! Cek Telegram.")
