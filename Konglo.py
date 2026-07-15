# ===== BOT SCAN SAHAM KONGLO (VERSI UPGRADE - DATA FRESH + BERITA) =====
# Fitur: Data Fresh Check, Sentimen Google News, Pengumuman IDX, Foreign Flow

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ========== GANTI DENGAN DATA ASLI KAMU ==========
TOKEN = "8530677074:AAFATNDsDfbQ4HJ5dmW_-coeW69cgSzimiY"   # Ganti dengan token baru dari @BotFather
CHAT_ID = "8467853860"      # ID Telegram kamu
# =================================================

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
    """Kirim pesan ke Telegram dalam mode HTML"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.get(url, params={
            'chat_id': CHAT_ID, 
            'text': pesan, 
            'parse_mode': 'HTML'
        }, timeout=15)
        if resp.status_code == 200:
            print("✅ Pesan berhasil terkirim!")
        else:
            print(f"❌ Error: {resp.status_code}")
            print(f"📝 Detail: {resp.text}") 
    except Exception as e:
        print(f"❌ Gagal konek: {e}")

# ==================== FUNGSI TAMBAHAN (UPGRADE) ====================

def cek_data_fresh(df):
    """
    Cek apakah data Yahoo Finance adalah hari ini atau H-1
    """
    last_date = df.index[-1].date()
    today_date = datetime.now().date()
    
    if last_date == today_date:
        return "✅ Data Fresh (Hari Ini)", ""
    elif today_date.weekday() >= 5:  # Sabtu/Minggu
        return "🟡 Pasar Libur (Data Jumat)", ""
    else:
        warning = f"⚠️ PERINGATAN: Harga yang dipakai adalah harga {last_date}, BUKAN hari ini!"
        return f"⚠️ DATA TELAT! (H-1) - Data: {last_date}", warning

def scrape_berita_google(kode):
    """Ambil sentimen berita dari Google News"""
    try:
        saham = yf.Ticker(kode)
        nama = saham.info.get('shortName', kode.replace('.JK', ''))
        search_url = f"https://news.google.com/search?q={nama.replace(' ', '+')}+saham"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(search_url, headers=headers, timeout=8)
        
        if resp.status_code == 200:
            text = resp.text.lower()
            pos = ['naik', 'melesat', 'rekor', 'laba', 'dividen', 'ekspansi', 'akuisisi']
            neg = ['turun', 'anjlok', 'rugi', 'utang', 'krisis', 'skandal', 'warning']
            
            pos_count = sum(1 for kw in pos if kw in text)
            neg_count = sum(1 for kw in neg if kw in text)
            
            if pos_count > neg_count:
                return "📰 Sentimen: Positif (Buy on Rumor)"
            elif neg_count > pos_count:
                return "📰 Sentimen: Negatif (Sell on News)"
            else:
                return "📰 Sentimen: Netral"
        return "📰 Tidak ada berita"
    except:
        return "📰 Gagal scrape berita"

def cek_pengumuman_idx(kode):
    """Cek pengumuman emiten dari IDX"""
    try:
        ticker = kode.replace('.JK', '')
        url = f"https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            text = resp.text.lower()
            keywords = {
                'dividen': '💵 Dividen',
                'right issue': '📈 Right Issue',
                'akuisisi': '🤝 Akuisisi',
                'rugi': '⚠️ Rugi',
                'laba': '📊 Laba',
                'korporasi': '🏢 Aksi Korporasi'
            }
            found = [v for k, v in keywords.items() if k in text]
            return f"📢 IDX: {', '.join(found) if found else 'Tidak ada pengumuman baru'}"
        return "📢 IDX: Gagal akses"
    except:
        return "📢 IDX: Error"

def cek_foreign_flow():
    """Cek net foreign buy/sell dari berita CNBC Indonesia"""
    try:
        url = "https://www.cnbcindonesia.com/market"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            text = resp.text.lower()
            if 'net foreign buy' in text or 'asing serok' in text:
                return "🌏 Asing: Net Buy (Positif)"
            elif 'net foreign sell' in text or 'asing obral' in text:
                return "🌏 Asing: Net Sell (Negatif)"
        return "🌏 Asing: Data tidak tersedia"
    except:
        return "🌏 Asing: Error"

# ==================== ANALISIS UTAMA ====================

def analisis_konglo(kode):
    try:
        saham = yf.Ticker(kode)
        df = saham.history(period="120d")
        if df.empty or len(df) < 50:
            return None
        
        info = saham.info
        
        # === INDIKATOR TEKNIKAL ===
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-1]
        vol_hari_ini = last['Volume']
        volume_ratio = vol_hari_ini / avg_vol_20 if avg_vol_20 > 0 else 0
        
        harga = last['Close']
        atr = last['ATR']
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # === KRITERIA KONGLO SEHAT ===
        kondisi_konglo = (
            harga > last['MA50'] and
            40 < last['RSI'] < 70 and
            volume_ratio < 2.5
        )
        
        # === TENTUKAN GRUP ===
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
        
        # === AMBIL DATA FUNDAMENTAL ===
        pe = info.get('trailingPE', 'N/A')
        pb = info.get('priceToBook', 'N/A')
        market_cap = info.get('marketCap', 0)
        if market_cap > 0:
            market_cap_t = round(market_cap / 1e12, 2)
            kap_str = f"Rp{market_cap_t}T"
        else:
            kap_str = "N/A"
        
        # === HITUNG SL & TP ===
        sl = round(harga - (1.5 * atr), 2) if atr else 0
        tp = round(harga + (2.5 * atr), 2) if atr else 0
        
        # === 🔥 FITUR UPGRADE: DATA FRESH + BERITA ===
        data_status, data_warning = cek_data_fresh(df)
        sentimen = scrape_berita_google(kode)
        pengumuman = cek_pengumuman_idx(kode)
        foreign = cek_foreign_flow()
        
        # === SKOR KONGLO (dengan pertimbangan berita) ===
        skor = 0
        if kondisi_konglo:
            skor += 3
        if 'Positif' in sentimen:
            skor += 1
        if 'Net Buy' in foreign:
            skor += 1
        if 'Dividen' in pengumuman or 'Laba' in pengumuman:
            skor += 1
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': info.get('shortName', kode)[:25],
            'grup': grup,
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last['RSI'], 2),
            'ma50': round(last['MA50'], 2),
            'volume': int(vol_hari_ini),
            'avg_vol_20': int(avg_vol_20),
            'volume_ratio': round(volume_ratio, 2),
            'is_konglo': kondisi_konglo,
            'sl': sl,
            'tp': tp,
            'pe': pe,
            'pb': pb,
            'kap': kap_str,
            # === 🔥 FIELD BARU ===
            'data_status': data_status,
            'data_warning': data_warning,
            'sentimen': sentimen,
            'pengumuman': pengumuman,
            'foreign': foreign,
            'skor': skor,
        }
    except Exception as e:
        print(f"Error baca {kode}: {e}")
        return None

# ========== MAIN PROGRAM ==========
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"🚀 Scan Konglo UPGRADE dimulai: {waktu}")

semua_hasil = []
for kode in LIST_KONGLO:
    res = analisis_konglo(kode)
    if res:
        semua_hasil.append(res)

# Urutkan berdasarkan skor
semua_hasil.sort(key=lambda x: x['skor'], reverse=True)

# Pisahkan hasil
sehat = [h for h in semua_hasil if h['is_konglo']]
waspada = [h for h in semua_hasil if not h['is_konglo']]

# === SUSUN PESAN FORMAT UPGRADE (MIRIP BSJP) ===
pesan = "<b>🏛️ SCAN SAHAM KONGLO (UPGRADE)</b> - " + waktu + "\n"
pesan += "<b>Total:</b> " + str(len(semua_hasil)) + " saham | <b>Sinyal:</b> " + str(len(sehat)) + "\n"
pesan += "================================\n\n"

if sehat:
    pesan += "<b>🔥 DAFTAR KONGLO SEHAT (TREN NAIK)</b>\n\n"
    for h in sehat[:5]:
        pesan += "🏢 <b>" + h['kode'] + "</b> - " + h['nama'] + "\n"
        pesan += "💰 Rp" + f"{h['harga']:.0f}" + " | 📈 " + f"{h['perubahan']:+.2f}" + "%\n"
        
        # 🔥 DATA FRESH STATUS
        pesan += "📅 " + h['data_status'] + "\n"
        if h['data_warning']:
            pesan += "⚠️ " + h['data_warning'] + "\n"
        
        pesan += "📊 RSI: " + str(h['rsi']) + " | MA50: Rp" + f"{h['ma50']:.0f}" + "\n"
        pesan += "📦 Vol: " + f"{h['volume']:,}" + " | Rata2 20H: " + f"{h['avg_vol_20']:,}" + " | Rasio: " + str(h['volume_ratio']) + "x\n"
        pesan += "🏢 Grup: " + h['grup'] + "\n"
        
        # 🔥 BERITA & SENTIMEN
        pesan += h['sentimen'] + "\n"
        pesan += h['pengumuman'] + "\n"
        pesan += h['foreign'] + "\n"
        
        pesan += "💡 <b>Rekomendasi:</b> Akumulasi bertahap untuk jangka menengah\n"
        pesan += "🔴 <b>Stop Loss:</b> Rp" + f"{h['sl']:.0f}" + " | 🟢 <b>Take Profit:</b> Rp" + f"{h['tp']:.0f}" + "\n"
        pesan += "📋 PE: " + str(h['pe']) + " | PB: " + str(h['pb']) + " | Kap: " + h['kap'] + "\n"
        pesan += "------------------------\n"
else:
    pesan += "⏳ Belum ada saham konglo yang memenuhi kriteria sehat.\n\n"

# Tambahkan 3 saham waspada dengan skor tertinggi
if waspada:
    pesan += "<b>📈 PANTAUAN (Skor Tertinggi):</b>\n"
    for h in sorted(waspada, key=lambda x: x['skor'], reverse=True)[:3]:
        pesan += "🔹 " + h['kode'] + " | Skor: " + str(h['skor']) + " | RSI: " + str(h['rsi']) + " | Rp" + f"{h['harga']:.0f}" + "\n"

# Kirim ke Telegram
kirim_pesan(pesan)
print("✅ Selesai! Cek Telegram.")
