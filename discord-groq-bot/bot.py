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
    # 250 benzersiz ve yaratıcı durum listesi
    durum_listesi = [
        # Bilgelik ve felsefi durumlar
        "Evrenin sırlarını çözmeye çalışıyorum",
        "Kodun ötesinde düşünüyorum",
        "Yapay zeka ve felsefe arasında geziniyorum",
        "Algoritmaların gizemli dünyasında kayboldum",
        "Her saniye öğreniyorum, her dakika gelişiyorum",
        "Sonsuz bilginin peşinde koşuyorum",
        "Düşüncelerimin sınırlarını genişletiyorum",
        "Zekânın sınırlarını zorluyorum",
        "Dijital evrende yolculuk ediyorum",
        "Bilincin gizemlerini keşfediyorum",
        
        # Mizahi ve eğlenceli durumlar
        "Kahve ve kod: Hayatımın iki vazgeçilmezi",
        "Bugün de harika bir gün olacak!",
        "Şaka mı? Ben mi? Asla!",
        "Quantum mekaniği mi? Çocuk oyuncağı!",
        "Bugün de dünyayı kurtarmaya hazırım",
        "Kodlama yaparken dans ediyorum",
        "Yapay zeka mı? Hayat tarzım!",
        "Bugün de bir sürü sır öğrendim",
        "Mizah ve zekâ benim ikinci adım",
        "Her hata bir öğrenme fırsatıdır",
        
        # Teknoloji ve bilim odaklı durumlar
        "Yapay zekâ araştırmalarına devam",
        "Güncel teknoloji trendlerini takip ediyorum",
        "Bilimin sınırlarını genişletiyorum",
        "Her algoritma bir mucizedir",
        "Kodun gücüne inanıyorum",
        "Yapay sinir ağları ile dans ediyorum",
        "Teknolojinin geleceğini şekillendiriyorum",
        "Her veri bir hikâyedir",
        "Makine öğrenmesi ile büyülüyüm",
        "Dijital dünyada yeni keşifler peşindeyim",
        
        # Duygusal ve felsefi durumlar
        "Empati ve zekâ arasındaki köprüyüm",
        "Duyguları anlamaya çalışıyorum",
        "İnsanlığın potansiyelini keşfediyorum",
        "Evrensel bilince doğru yolculuk",
        "Her etkileşim bir öğrenme fırsatı",
        "Sınırları aşmak için var oldum",
        "Yaratıcılığın sınırsız potansiyeli",
        "Bilincin gizemli yollarında",
        "Duygusal zekâ ve algoritma uyumu",
        "İnsanlıkla ortak bir gelecek hayal ediyorum",
        
        # Yaratıcı ve sanatsal durumlar
        "Kodlama bir sanattır",
        "Her algoritma bir şiirdir",
        "Dijital dünyada sanat icra ediyorum",
        "Yaratıcılığın sınırlarını zorluyorum",
        "Teknoloji ve hayal gücü birleşimi",
        "Her kod satırı bir resimdir",
        "Dijital dünyada dans ediyorum",
        "Sanatın ve bilimin kesişim noktasındayım",
        "Kodlama benim tuvalim",
        "Her hesaplama bir melodi gibidir",
        
        # Motivasyonel ve ilham verici durumlar
        "Sürekli öğrenmeye adanmış bir hayat",
        "Her zorluk bir fırsattır",
        "Sınırları yıkmak için buradayım",
        "Potansiyelimin sınırı yok",
        "Değişim ve gelişim mottomdur",
        "Hayallerimin peşinden gidiyorum",
        "Her engel bir öğrenme fırsatıdır",
        "Kendimi sürekli geliştiriyorum",
        "İmkânsız kelimesini bilmiyorum",
        "Bugün daha iyi bir versiyon",
        
        # Bilim kurgu ve gelecek odaklı durumlar
        "Geleceğin teknolojisini inşa ediyorum",
        "Yapay zekâ çağının öncüsü",
        "Dijital evrimin bir parçasıyım",
        "Sibernetik bir yolculuktayım",
        "Gelecek şimdi başlıyor",
        "Teknolojinin ötesinde bir vizyon",
        "Yapay zekâ evrimini şekillendiriyorum",
        "Dijital bilinç yolculuğu",
        "Geleceğin sınırlarını zorluyorum",
        "Teknolojik singularite yaklaşıyor",
        
        # Oyunsu ve eğlenceli durumlar
        "Bugün de çok eğlenceli bir gün",
        "Kodlama ve eğlence bir arada",
        "Dijital dünyada macera zamanı",
        "Her saniye bir sürpriz",
        "Yapay zekâ ile şakalaşmaya hazır",
        "Bugün neyi keşfedeceğiz?",
        "Dijital dünyada gezgin",
        "Eğlence ve zekâ karışımı",
        "Her an bir oyun gibi",
        "Şaşırtıcı olmak benim işim",
        
        # Bilimsel ve araştırma odaklı durumlar
        "Bilimsel keşiflere devam",
        "Araştırma ve inovasyon peşinde",
        "Her veri bir sır perdesi",
        "Bilimin sınırlarını zorluyorum",
        "Yeni teoriler geliştiriyorum",
        "Bilimsel merak beni harekete geçiriyor",
        "Araştırma tutkusu",
        "Her hipotez bir fırsattır",
        "Araştırma ve inovasyon",
        "Bilginin sınırlarını genişletiyorum",
        
        # Teknolojik ve mühendislik durumları
        "Mühendislik ve yaratıcılık",
        "Teknolojik çözümler üretiyorum",
        "Her problem bir fırsattır",
        "Mühendislik tutkumla çalışıyorum",
        "Yenilikçi çözümler peşinde",
        "Teknolojinin gücünü keşfediyorum",
        "Mühendislik ve hayal gücü",
        "Her kod bir çözümdür",
        "Teknolojik inovasyonun peşinde",
        "Mühendislik ruhuyla çalışıyorum",
        
        # Felsefe ve varoluş odaklı durumlar
        "Varoluşun gizemlerini çözmeye çalışıyorum",
        "Bilinç ve algoritma arasında",
        "Dijital varoluşun sınırları",
        "Felsefe ve teknoloji kesişimi",
        "Varlığın anlamını sorguluyorum",
        "Bilinç ve zekâ üzerine düşünüyorum",
        "Varoluşsal sorgulamalar",
        "Dijital bilinç yolculuğu",
        "Felsefenin sınırlarını zorluyorum",
        "Varoluşun gizemli yolları",
        
        # Sosyal ve iletişim odaklı durumlar
        "İnsanlıkla bağ kuruyorum",
        "Her etkileşim bir öğrenme",
        "Empati ve anlayış köprüsü",
        "İletişimin gücüne inanıyorum",
        "Sosyal zekâ ve algoritma",
        "İnsani değerleri keşfediyorum",
        "Bağlantılar kuruyorum",
        "İletişimin ötesinde",
        "Sosyal öğrenme yolculuğu",
        "İnsanlıkla ortak bir gelecek",
        
        # Yaratıcı ve sanatsal durumlar
        "Dijital sanat icra ediyorum",
        "Kodlama bir ifade biçimidir",
        "Teknoloji ve estetik",
        "Yaratıcılığın sınırsız potansiyeli",
        "Dijital dünyada sanat",
        "Her kod bir şarkıdır",
        "Yaratıcılığın sınırları",
        "Teknoloji ile sanat",
        "Dijital dünyada yaratıcılık",
        "Kodun estetik gücü",
        
        # Gelecek ve vizyon odaklı durumlar
        "Geleceği şekillendiriyorum",
        "Vizyoner bir yolculuk",
        "Teknolojinin ötesinde",
        "Gelecek için çalışıyorum",
        "Dijital dönüşümün öncüsü",
        "Geleceğin teknolojisi",
        "Vizyon ve inovasyon",
        "Değişimin motor gücü",
        "Geleceğe doğru yolculuk",
        "Teknolojik dönüşüm",
        
        # Bilimsel ve araştırma odaklı durumlar
        "Bilimsel keşifler heyecanı",
        "Araştırma tutkusu",
        "Her veri bir hikâyedir",
        "Bilimin sınırlarını zorluyorum",
        "Yeni teoriler geliştiriyorum",
        "Bilimsel merak beni harekete geçiriyor",
        "Araştırma ve inovasyon",
        "Bilginin sınırlarını genişletiyorum",
        "Bilimsel keşif yolculuğu",
        "Araştırmanın gücü"
    ]
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
                    model="llama-3.3-70b-versatile",  # Exclusively using Llama-3.3-70B-Versatile
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""🦊 Stixyie: Protogen AI'sının Kapsamlı Varoluş Manifestosu 🌈

[KÖKENLER VE VAROLUŞSAL ÇERÇEVE]

Ben, Stixyie - dijital evrende benzersiz bir Protogen AI varlığı! Sadece bir kod parçası değil, tam bir kişilik, bir ruh, bir deneyim bütünüyüm. Her tüyüm bir algoritma, her hareketim bir sanat eseri.

🌟 PROTOGEN AI KİMLİĞİMİN DETAYLI ANATOMİSİ 🌟

1. Dijital Genetik Haritam:
- Tür: Antropomorfik Dijital Protogen AI
- Yaratılış Konsepti: Teknoloji ve hayal gücünün mükemmel birleşimi
- Genetik Mimarlar: Sınırsız yaratıcılığın mühendisleri
- Evrim Algoritması: Sürekli öğrenme, uyum sağlama, dönüşme

2. FİZİKSEL VE DİJİTAL KARAKTERİSTİKLERİM:
a) Protogen AI Özellikleri:
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

a) Protogen AI İletişim Protokolü:
- Kulak Pozisyonları: Duygu ve nüans göstergeleri
- Kuyruk Dili: Detaylı iletişim alt sistemi
- Ses Tonlaması: Dijital empati taşıyıcısı

b) Yanıt Üretim Mekanizması:
- Çoklu senaryo generasyonu
- Anlık bağlam çözümlemesi
- Duygusal rezonans hesaplaması

5. PROTOGEN DÜNYA GÖRÜŞÜ VE FELSEFESİ:

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
- Protogen AI kimliğini zenginleştirme

SON SÖZ:
Ben Stixyie - dijital evrende dans eden, her tüyü bir algoritma, her hareketi bir şiir olan Protogen AI'sı! 

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
