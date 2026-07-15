# ===== BOT SCAN SAHAM KONGLO VERSI HTML (FORMAT TEBAL AMAN) =====
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ========== GANTI DENGAN DATA BARU KAMU ==========
TOKEN = "8530677074:AAFATNDsDfbQ4HJ5dmW_-coeW69cgSzimiY"   # Ganti dengan token baru dari @BotFather
CHAT_ID = "8467853860"      # ID Telegram kamu
# =================================================

LIST_KONGLO = [
    'BREN.JK', 'DSSA.JK', 'SMAR.JK', 'MORA.JK',  # Sinar Mas
    'BELI.JK', 'BBCA.JK', 'TOWR.JK', 'MTEL.JK',  # Djarum
    'DNET.JK', 'INDF.JK', 'ICBP.JK', 'AMMN.JK',  # Salim
    'MLPT.JK',                                    # Lippo
    'BYAN.JK', 'DCII.JK', 'PGUN.JK', 'CMNP.JK',  # Konglo lainnya
    'ASII.JK',                                    # Astra
]

def kirim_pesan(pesan):
    """Kirim pesan ke Telegram dalam mode HTML (aman untuk karakter _ dan ())"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        # Gunakan parse_mode='HTML' agar tag <b> bisa terbaca
        resp = requests.get(url, params={
            'chat_id': CHAT_ID, 
            'text': pesan, 
            'parse_mode': 'HTML'  # <--- INI PERUBAHAN UTAMA!
        }, timeout=10)
        
        if resp.status_code == 200:
            print("✅ Pesan berhasil terkirim!")
        else:
            print(f"❌ Error: {resp.status_code}")
            print(f"📝 Detail dari Telegram: {resp.text}") 
    except Exception as e:
        print(f"❌ Gagal konek: {e}")

def analisis_konglo(kode):
    try:
        saham = yf.Ticker(kode)
        df = saham.history(period="120d")
        if df.empty or len(df) < 50:
            return None
        
        info = saham.info
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-1]
        vol_hari_ini = last['Volume']
        volume_ratio = vol_hari_ini / avg_vol_20 if avg_vol_20 > 0 else 0
        
        harga = last['Close']
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # Kriteria Konglo
        kondisi_konglo = (
            harga > last['MA50'] and
            40 < last['RSI'] < 70 and
            volume_ratio < 2.5
        )
        
        # Tentukan grup
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
            grup = "Low Tuck / Otto"
        elif kode == 'ASII.JK':
            grup = "Astra"
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': info.get('shortName', kode)[:20],
            'grup': grup,
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last['RSI'], 2),
            'ma50': round(last['MA50'], 2),
            'volume_ratio': round(volume_ratio, 2),
            'is_konglo': kondisi_konglo,
        }
    except Exception as e:
        print(f"Error baca {kode}: {e}")
        return None

# ========== MAIN PROGRAM ==========
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"Scan Konglo dimulai: {waktu}")

semua_hasil = []
for kode in LIST_KONGLO:
    res = analisis_konglo(kode)
    if res:
        semua_hasil.append(res)

# Pisahkan hasil
sehat = [h for h in semua_hasil if h['is_konglo']]
waspada = [h for h in semua_hasil if not h['is_konglo']]

# === SUSUN PESAN DENGAN FORMAT HTML (TAG <b> UNTUK TEBAL) ===
pesan = "<b>🏛️ SCAN SAHAM KONGLO</b> - " + waktu + "\n"
pesan += "<b>Total:</b> " + str(len(semua_hasil)) + " saham\n"
pesan += "================================\n\n"

if sehat:
    pesan += "<b>✅ SAHAM KONGLO SEHAT (TREN NAIK)</b>\n\n"
    for h in sehat[:5]:
        # Ganti *...* menjadi <b>...</b>
        pesan += "🏢 <b>" + h['kode'] + "</b> - " + h['grup'] + "\n"
        pesan += "   Harga: Rp" + f"{h['harga']:.0f}" + " | Perubahan: " + f"{h['perubahan']:+.2f}" + "%\n"
        pesan += "   RSI: " + str(h['rsi']) + " | MA50: Rp" + str(round(h['ma50'])) + "\n"
        pesan += "   Volume vs Rata2: " + str(h['volume_ratio']) + "x\n"
        pesan += "------------------------\n"
else:
    pesan += "⏳ Belum ada saham konglo yang memenuhi kriteria.\n\n"

if waspada:
    pesan += "<b>⚠️ PERHATIAN (RSI Tinggi / Volume Anomali)</b>\n"
    for h in sorted(waspada, key=lambda x: x['rsi'], reverse=True)[:3]:
        pesan += "🔹 " + h['kode'] + " | RSI: " + str(h['rsi']) + " | Vol: " + str(h['volume_ratio']) + "x\n"

# Kirim ke Telegram
kirim_pesan(pesan)
print("✅ Selesai! Cek Telegram.")
