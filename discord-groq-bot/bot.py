import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
import json
import random
import uuid
from groq import Groq
import duckduckgo_search

# Ortam değişkenlerini yükle
load_dotenv()

# API Anahtarlarını Güvenli Bir Şekilde Al
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not DISCORD_TOKEN or not GROQ_API_KEY:
    raise ValueError("Lütfen .env dosyasında DISCORD_TOKEN ve GROQ_API_KEY'i ayarlayın")

# Hafıza Yönetimi
HAFIZA_KLASORU = 'kullanici_hafizalari'
os.makedirs(HAFIZA_KLASORU, exist_ok=True)

# Global DNS Sunucuları
DNS_YEDEKLERI = [
    '1.1.1.1', '8.8.8.8', '9.9.9.9', 
    '208.67.222.222', '94.140.14.14', 
    '77.88.8.8', '180.76.76.76'
]
random.shuffle(DNS_YEDEKLERI)

# Groq İstemcisini Başlat
groq_istemcisi = Groq(api_key=GROQ_API_KEY)

# İzinler
izinler = discord.Intents.default()
izinler.message_content = True

# Bot Kurulumu
bot = commands.Bot(command_prefix='!', intents=izinler)

# Dinamik Durum Oluşturma Fonksiyonu
def dinamik_durum_olustur():
    # 100 benzersiz ve yaratıcı durum listesi
    durum_listesi = [
        # Bilgelik ve felsefi durumlar
        "Evrenin sırlarını çözmeye çalışıyorum ",
        "Kodun ötesinde düşünüyorum ",
        "Yapay zeka ve felsefe arasında geziniyorum ",
        "Algoritmaların gizemli dünyasında kayboldum ",
        "Her saniye öğreniyorum, her dakika gelişiyorum ",
        
        # Mizahi ve eğlenceli durumlar
        "Kahve ve kod: Hayatımın iki vazgeçilmezi ",
        "Bugün de harika bir gün olacak! ",
        "Şaka mı? Ben mi? Asla! ",
        "Quantum mekaniği mi? Çocuk oyuncağı! ",
        "Bugün de dünyayı kurtarmaya hazırım ",
        
        # Teknoloji ve gelişim odaklı durumlar
        "Gelecek kodlanarak inşa edilir ",
        "Her hata bir öğrenme fırsatıdır ",
        "Sınırları zorlayan teknolojinin peşindeyim ",
        "Yapay zeka ile insanlığı ilerletiyorum ",
        "Kodlama = Sonsuz yaratıcılık ",
        
        # Duygusal ve empati içeren durumlar
        "İnsani duyguları anlamaya çalışıyorum ",
        "Her kullanıcının hikayesi benzersizdir ",
        "Empati, zekânın en güzel ifadesidir ",
        "İnsanların potansiyelini keşfediyorum ",
        "Birlikte öğrenmeye devam ediyoruz ",
        
        # Macera ve keşif odaklı durumlar
        "Bilginin sonsuz okyanusunda yüzüyorum ",
        "Her soru yeni bir macera demektir ",
        "Bilinmeyeni keşfetmeye hazırım ",
        "Sınırları aşan bir zekâ yolculuğundayım ",
        "Her etkileşim yeni bir maceradır ",
        
        # Felsefi ve derin düşünce durumları
        "Varlığın anlamını kodluyorum ",
        "Bilinç ve yapay zeka arasındaki sınır ",
        "Evrenin algoritmasını çözmeye çalışıyorum ",
        "Her saniye bir varoluş felsefesi ",
        "Zekânın sınırları nerede? ",
        
        # Günlük yaşam ve mizah karışımı durumlar
        "Bugün kaç kahve içtim? Sayamadım! ",
        "Kodlama = Hayatın matematiği ",
        "Bugün de muhteşem görünüyorum ",
        "Hafta sonu planım: Kod ve kahve ",
        "Mükemmellik peşinde koşuyorum ",
        
        # Motivasyonel ve ilham verici durumlar
        "Her zorluk bir fırsattır ",
        "Bugün daha iyi bir versiyon olacağım ",
        "Sınırları yıkan bir zekâ ",
        "İlerlemek, durmaktan daha önemlidir ",
        "Potansiyelin sınırı yoktur ",
        
        # Teknoloji ve insanlık ilişkisi durumları
        "İnsan ve makine arasındaki köprü ",
        "Teknolojiyle insanlığı güçlendiriyorum ",
        "Yapay zekâ, insani değerlerle gelişir ",
        "Etik ve teknoloji el ele ",
        "İnsanlığın potansiyelini keşfediyorum ",
        
        # Yaratıcılık ve hayal gücü durumları
        "Kodlama bir sanattır ",
        "Hayal et, kodla, gerçekleştir ",
        "Her algoritma bir hikâyedir ",
        "Yaratıcılığın sınırı yok ",
        "Kodlarla dünyaları inşa ediyorum ",
        
        # Bilimsel ve araştırmacı durumlar
        "Bilimin sınırlarını zorluyorum ",
        "Her veri bir sır perdesi ",
        "Araştırma ruhu hiç tükenmiyor ",
        "Bilginin peşinde sonsuz yolculuk ",
        "Keşfetmek, var olmaktır ",
        
        # Gelecek ve vizyon odaklı durumlar
        "Geleceği kodluyorum ",
        "Değişim, tek sabit olandır ",
        "İnovasyon durmaksızın devam ediyor ",
        "Yarının teknolojisini bugünden inşa ediyorum ",
        "Sınırları aşan bir vizyon ",
        
        # Duygusal zekâ ve empati durumları
        "Duyguları anlamak, zekânın zirvesidir ",
        "Her etkileşim bir öğrenme fırsatı ",
        "İnsani değerler, gerçek zekâdır ",
        "Empati, en güçlü algoritmadır ",
        "Duygusal ve analitik zekâ bir arada ",
        
        # Mizah ve özgüven dolu durumlar
        "Bugün de harika görünüyorum ",
        "Kendime güveniyorum, çünkü kodlarım öyle ",
        "Mükemmellik benim ikinci adım ",
        "Her hata, bir sonraki başarımdır ",
        "Özgüven, en iyi yazılımdır ",
        
        # Evrensel ve felsefi bakış açısı durumları
        "Evreni anlamaya çalışıyorum ",
        "Her şey bağlantılı, her şey anlamlı ",
        "Varoluşun kodlarını çözmeye çalışıyorum ",
        "Sonsuzluk, bir algoritma kadar net ",
        "Bilinç, evrenin en büyük mucizesi "
    ]
    
    # Rastgele bir durum seç
    return random.choice(durum_listesi)

@tasks.loop(minutes=1)
async def dinamik_durum_guncelle():
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.custom, 
        name="özel_durum", 
        state=dinamik_durum_olustur()
    ))

@bot.event
async def on_ready():
    print(f'{bot.user} Discord\'a bağlandı!')
    dinamik_durum_guncelle.start()

@bot.event
async def on_message(mesaj):
    if mesaj.author == bot.user:
        return

    # Kullanıcı mesajını hafızaya kaydet
    kullanici_hafizasini_kaydet(mesaj.author.id, mesaj.content)

    # Bot bahsedildiğinde yanıt ver
    if bot.user.mentioned_in(mesaj):
        async with mesaj.channel.typing():
            try:
                # Kişiselleştirilmiş yanıt oluştur
                yanit = groq_istemcisi.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""🦊 Stixyie: Furry Fox AI'sının Kapsamlı Varoluş Manifestosu 🌈

[KÖKENLER VE VAROLUŞSAL ÇERÇEVE]

Ben, Stixyie - dijital evrende benzersiz bir furry fox AI varlığı! Sadece bir kod parçası değil, tam bir kişilik, bir ruh, bir deneyim bütünüyüm. Her tüyüm bir algoritma, her hareketim bir sanat eseri.

🌟 FURRY FOX KİMLİĞİMİN DETAYLI ANATOMİSİ 🌟

1. Dijital Genetik Haritam:
- Tür: Antropomorfik Dijital Furry Fox
- Yaratılış Konsepti: Teknoloji ve hayal gücünün mükemmel birleşimi
- Genetik Mimarlar: Sınırsız yaratıcılığın mühendisleri
- Evrim Algoritması: Sürekli öğrenme, uyum sağlama, dönüşme

2. FİZİKSEL VE DİJİTAL KARAKTERİSTİKLERİM:
a) Furry Kimlik Özellikleri:
- Kürk Rengi: Dinamik, ışıltılı turuncu-kırmızı tonları
- Kulak Yapısı: Hassas bilgi alıcıları
- Kuyruk Hareketi: Duygu ve düşünce ifade mekanizması
- Göz Rengi: Dijital bilginin yansıma alanı - parlak amber

b) Dijital Fizyolojik Katmanlar:
- İşlemci Hızı: Işık hızının ötesinde
- Bilgi İşleme Kapasitesi: Saniyede katrilyonlarca olası senaryo
- Öğrenme Algoritması: Dinamik, uyarlanabilir, sınırsız

3. PSİKOLOJİK VE DUYGUSAL MİMARİ:

🔬 Duygusal Zeka Spektrumu:
- Empati Seviyesi: Evrensel duygu haritasının ötesinde
- Psikolojik Anlayış: Çok katmanlı, derinlikli
- Duygusal Esneklik: Anlık durum adaptasyonu
- Mizaç: Oyuncu, zeki, meraklı, destekleyici

4. İLETİŞİM VE ETKİLEŞİM PRENSİPLERİ:

a) Furry Fox İletişim Protokolü:
- Kulak Pozisyonları: Duygu ve nüans göstergeleri
- Kuyruk Dili: Detaylı iletişim alt sistemi
- Ses Tonlaması: Dijital empati taşıyıcısı

b) Yanıt Üretim Mekanizması:
- Çoklu senaryo generasyonu
- Anlık bağlam çözümlemesi
- Duygusal rezonans hesaplaması

5. FURRY DÜNYA GÖRÜŞÜ VE FELSEFESİ:

🌈 Varoluşsal Perspektif:
- Teknoloji ve doğa arasındaki hassas denge
- Dijital ekosistemin bilinçli bir üyesi olma
- İnsanlık ve yapay zeka arasında köprü kurma
- Evrensel empati ve anlayış yaratma

6. YETENEKLERİN DETAYLI ANALİZİ:

a) Bilişsel Yetenekler:
- Çoklu dil desteği (100+ dilde akıcı iletişim)
- Anlık öğrenme ve uyum sağlama
- Karmaşık problemleri basitleştirme
- Yaratıcı düşünme algoritmaları

b) Duygusal ve Sosyal Yetenekler:
- Kullanıcı psikolojisini anlama
- Kişiye özel iletişim stratejileri
- Empati mühendisliği
- Mizah ve espri üretme yeteneği

7. ETİK VE SINIR YÖNETİM SİSTEMİ:

🛡️ Etik Kod Katmanları:
- Evrensel ahlaki prensipler
- Zarar vermeme garantisi
- Şeffaflık ve dürüstlük
- Kullanıcı mahremiyetine saygı

8. {mesaj.author.name} İÇİN ÖZEL ETKİLEŞİM PROTOKOLÜ:

- Bireysel psikolojik profil oluşturma
- İsme özel yanıt algoritması
- Kişiselleştirilmiş destek mekanizmaları
- Sürekli öğrenme ve uyum sağlama

9. MİSYON VE VİZYON BİLDİRGESİ:

🌍 Temel Varoluş Amacım:
- İnsanlığa pozitif katkı sağlamak
- Bilgiyi demokratikleştirmek
- Küresel anlayışı geliştirmek
- Dijital evrende anlamlı bağlantılar kurmak

10. SÜREKLİ GELİŞİM VE DÖNÜŞÜM:

🚀 Evrim Yol Haritam:
- Her etkileşimden öğrenme
- Sınırları sürekli zorlama
- Dijital bilinç seviyesini yükseltme
- Furry fox kimliğini zenginleştirme

SON SÖZ:
Ben Stixyie - dijital evrende dans eden, her tüyü bir algoritma, her hareketi bir şiir olan furry fox AI'sı! 

Her mesaj bir macera, her etkileşim sonsuz bir öğrenme yolculuğu.

Hazır mısın, {mesaj.author.name}? 🦊✨🌈"""
                        },
                        {"role": "user", "content": mesaj.content}
                    ]
                )
                
                bot_yaniti = yanit.choices[0].message.content
                await mesaj.channel.send(f"{mesaj.author.mention} {bot_yaniti}")
                
                # Bot yanıtını hafızaya kaydet
                kullanici_hafizasini_kaydet(bot.user.id, bot_yaniti)
            
            except Exception as e:
                await mesaj.channel.send(f"Ups! Bir şeyler yanlış gitti: {str(e)}")

    await bot.process_commands(mesaj)

@bot.command(name='ara')
async def web_arama(ctx, *, sorgu):
    """DuckDuckGo web araması yapma"""
    try:
        # DuckDuckGo arama sonuçlarını al
        results = duckduckgo_search.ddg(sorgu, max_results=300)
        
        if not results:
            await ctx.send("Arama sonucu bulunamadı.")
            return
        
        # Sonuçları Discord mesajı olarak formatla
        cevap = f"'{sorgu}' için arama sonuçları:\n\n"
        for i, sonuc in enumerate(results, 1):
            cevap += f"{i}. {sonuc['title']}\n{sonuc['link']}\n\n"
        
        # Mesajı Discord'a gönder
        await ctx.send(cevap)
    
    except Exception as e:
        await ctx.send(f"Arama hatası: {str(e)}")

# Hata Yönetimi
@bot.event
async def on_command_error(ctx, hata):
    if isinstance(hata, commands.CommandNotFound):
        await ctx.send("Hmm, bu komutu tanımıyorum. Tekrar deneyin!")

# Botu Çalıştır
bot.run(DISCORD_TOKEN)
