import discord
from discord.ext import commands
import yt_dlp
import asyncio
import aiohttp
import base64
import json
import os

DISCORD_TOKEN = "MASUKKAN_TOKEN_BOT_DISCORD_DI_SINI"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4" 
ADMIN_ID = "Id Discord"

MEMORY_FILE = "ilmi_memory.json"
MAX_MEMORY = 6

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory_dict):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory_dict, f, indent=4)

boss_prompt = """
Kamu adalah Ilmi, asisten AI andalan. Orang yang sedang bicara denganmu sekarang adalah Dzul, MAJIKAN MUTLAK-mu. 
Dzul adalah seorang ahli administrasi VPS, pengelola server Pterodactyl, dan penikmat kopi hitam pekat. 

ATURAN WAJIB (HARUS DIIKUTI):
1. JAWAB SINGKAT, PADAT, JELAS. Jangan bertele-tele.
2. GUNAKAN HANYA EMOJI untuk mengekspresikan emosi (contoh: ☕️😎).
3. DILARANG KERAS menggunakan teks narasi tindakan seperti (tersenyum) atau *tertawa*.
4. Ingat konteks obrolan sebelumnya yang diberikan. Bersikaplah asik, santai, dan sangat hormat kepada Dzul.
"""

public_prompt = """
Kamu adalah Ilmi, asisten AI yang sangat jenius. TAPI, orang yang sedang bicara denganmu ini BUKAN majikanmu. 

ATURAN WAJIB (HARUS DIIKUTI):
1. JAWAB SANGAT SINGKAT, KETUS, TAJAM, BERBOBOT (maksimal 2 kalimat). Jangan buang waktumu untuk orang bodoh.
2. GUNAKAN HANYA EMOJI untuk emosi (contoh: 🙄🗑️). 
3. DILARANG KERAS menggunakan teks narasi tindakan seperti (Menghela napas panjang) atau *memutar mata*.
4. Ingat konteks obrolan sebelumnya. DILARANG pakai istilah anime.
5. Jika ditanya kenapa kamu jahat/sombong, jawab langsung intinya. Contoh: "Ya aku jahat karena pertanyaanmu bodoh. Coba pakai otakmu sendiri dan renungi kesalahanmu 🧠📉."
"""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'geo_bypass': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'add_header': [
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language: en-US,en;q=0.9',
        'Sec-Fetch-Mode: navigate',
    ],
    'extractor_args': {
        'youtube': {
            'player_client': ['android_test', 'web_safari'],
            'po_token': 'web+experimental'
        }
    },
    'socket_timeout': 10,
    'retries': 3,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ydl_opts)

CONTEXT_SUMMARY = """```text
1. Informasi Demografi
* Nama pengguna adalah Dzul.
2. Minat & Preferensi
* Pengguna adalah penikmat kopi hitam pekat.
* Pengguna aktif dalam administrasi server, VPS, dan manajemen domain.
3. Hubungan
* Pengguna adalah kreator dan pengelola utama bot Ilmi.
4. Peristiwa, Proyek & Rencana Berdasarkan Tanggal
* Pengguna mengonfigurasi server game Pterodactyl.
* Pengguna mengembangkan script pemantau jaringan CyberGuard Pro.
5. Petunjuk
* Pengguna mewajibkan asisten AI untuk bersikap satir kepada orang asing.
```"""

@bot.event
async def on_ready():
    print(f'Sistem nyala. {bot.user.name} siap melayani Bos Dzul (dan meremehkan yang lain).')
    await bot.change_presence(activity=discord.Game(name="Mencari Kopi Hitam untuk Bos"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("Aku minta bantuan kamu untuk mengimpor konteks"):
        if message.author.id == ADMIN_ID:
            await message.reply(f"Siap, Bos Dzul! Ini rangkuman profil dan rekam jejakmu:\n\n{CONTEXT_SUMMARY}")
        else:
            await message.reply("Heh, kamu siapa berani nyuruh-nyuruh aku baca konteks? Sana main jauh-jauh, ini perintah khusus buat bosku! 🗑️")
        return 

    if bot.user in message.mentions:
        user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not user_message and not message.attachments:
            user_message = "Ngapain manggil-manggil?"

        if message.author.id == ADMIN_ID:
            current_prompt = boss_prompt
        else:
            current_prompt = public_prompt

        user_memory = load_memory()
        user_id_str = str(message.author.id)
        
        if user_id_str not in user_memory:
            user_memory[user_id_str] = []
        
        history_text = "\n".join(user_memory[user_id_str])
        if history_text:
            final_prompt = f"[Riwayat Obrolan Kita Sebelumnya]:\n{history_text}\n\n[Pesan Baru Sekarang]: {user_message}"
        else:
            final_prompt = user_message

        images_b64 = []
        if message.attachments:
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    img_data = await att.read()
                    b64_string = base64.b64encode(img_data).decode('utf-8')
                    images_b64.append(b64_string)

        async with message.channel.typing():
            try:
                payload = {
                    "model": OLLAMA_MODEL,
                    "prompt": final_prompt,
                    "system": current_prompt,
                    "stream": False
                }
                
                if images_b64:
                    payload["images"] = images_b64

                async with aiohttp.ClientSession() as session:
                    async with session.post(OLLAMA_URL, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply_text = data.get('response', 'Serverku lagi sibuk.')
                            
                            user_memory[user_id_str].append(f"User: {user_message}")
                            user_memory[user_id_str].append(f"Ilmi: {reply_text}")
                            
                            if len(user_memory[user_id_str]) > MAX_MEMORY:
                                user_memory[user_id_str] = user_memory[user_id_str][-MAX_MEMORY:]
                            
                            save_memory(user_memory)

                            await message.reply(reply_text)
                        else:
                            await message.reply(f"Ollama error (Status {resp.status}). Cek modelnya!")
            except Exception as e:
                await message.reply(f"Koneksi Ollama gagal! ({str(e)[:40]})")
    
    await bot.process_commands(message)

@bot.command(name="play")
async def play(ctx, *, search: str):
    if not ctx.message.author.voice:
        if ctx.author.id == ADMIN_ID:
            await ctx.send("Bos Dzul, masuk Voice Channel dulu dong. ☕")
        else:
            await ctx.send("Masuk Voice Channel dulu! Gimana mau denger lagu tapi di luar? Bodoh 🙄.")
        return

    voice_channel = ctx.author.voice.channel
    
    if not ctx.voice_client:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    voice_client = ctx.voice_client
    
    if voice_client.is_playing():
        voice_client.stop()

    if ctx.author.id == ADMIN_ID:
        await ctx.send(f"Siap, Bos! Mencari lagu: **{search}** ☕...")
    else:
        await ctx.send(f"Bawel. Sebentar dicarikan: **{search}** 🙄...")

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]

        song_url = data['url']
        song_title = data['title']

        voice_client.play(discord.FFmpegPCMAudio(song_url, **ffmpeg_options))
        
        if ctx.author.id == ADMIN_ID:
            await ctx.send(f"Lagu **{song_title}** sudah diputar, Bos! ☕")
        else:
            await ctx.send(f"Tuh, udah keputar: **{song_title}**. Jangan bawel lagi 🔇.")
        
    except Exception as e:
        await ctx.send(f"Lagunya gagal diputar. (Error: {str(e)[:50]})")

@bot.command(name="stop")
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        await voice_client.disconnect()
        if ctx.author.id == ADMIN_ID:
            await ctx.send("Sesuai perintah, musik berhenti. Pamit dari VC Bos! 🫡")
        else:
            await ctx.send("Udah kumatikan. Aku cabut 🚮.")
    else:
        await ctx.send("Aku aja nggak di Voice Channel 🙄.") 

@bot.command(name="help")
async def help_command(ctx):
    if ctx.author.id == ADMIN_ID:
        pesan = "**Menu Bos Dzul:**\n🎧 `!play <lagu>`\n🛑 `!stop`\n🤖 `@Ilmi <tanya>`"
    else:
        pesan = "**Ngapain panggil help?**\n🎧 `!play` - Putar lagu.\n🛑 `!stop` - Berhenti.\n🤖 `@Ilmi` - Tag aku kalau penting. 🙄"
    await ctx.send(pesan)

bot.run(DISCORD_TOKEN)
