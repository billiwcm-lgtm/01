import os
import json
import asyncio
import subprocess
import requests
import edge_tts

# Configurações de Ambiente
COOKIES_JSON = os.getenv("VIBES_COOKIES")

# Texto que será convertido no áudio gratuito do vídeo (mude como preferir)
TEXTO_DO_VIDEO = "Este é um exemplo de áudio gerado de forma totalmente gratuita e automática."
# Vozes sugeridas para pt-BR: "pt-BR-AntonioNeural" (Masculino) ou "pt-BR-FranciscaNeural" (Feminino)
VOZ_ESCOLHIDA = "pt-BR-AntonioNeural"

# Definição e Criação das Pastas
PASTA_AUDIOS = "audios_gerados"
PASTA_VIDEOS_MUDOS = "videos_mudos"
PASTA_FINAIS = "videos_finais"

for pasta in [PASTA_AUDIOS, PASTA_VIDEOS_MUDOS, PASTA_FINAIS]:
    os.makedirs(pasta, exist_ok=True)

# Caminhos dos arquivos dentro das pastas
AUDIO_INPUT = os.path.join(PASTA_AUDIOS, "audio_gerado.mp3")
VIDEO_SEM_AUDIO = os.path.join(PASTA_VIDEOS_MUDOS, "video_mudo.mp4")
VIDEO_FINAL = os.path.join(PASTA_FINAIS, "resultado_5s.mp4")

def formatar_cookies_para_header():
    try:
        cookies_list = json.loads(COOKIES_JSON)
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
    except Exception as e:
        print(f"❌ Erro nos cookies: {e}")
        return ""

async def gerar_audio_do_video_gratis():
    print(f"🎙️ Etapa: Convertendo texto em áudio usando Edge-TTS ({VOZ_ESCOLHIDA})...")
    try:
        # Inicializa o comunicador do Edge TTS
        communicate = edge_tts.Communicate(TEXTO_DO_VIDEO, VOZ_ESCOLHIDA)
        # Salva o arquivo de áudio diretamente na nossa pasta de áudios
        await communicate.save(AUDIO_INPUT)
        
        if os.path.exists(AUDIO_INPUT):
            print(f"✅ Áudio gerado com sucesso em: {AUDIO_INPUT}")
            return True
        return False
    except Exception as e:
        print(f"❌ Falha ao gerar áudio com Edge-TTS: {e}")
        return False

def gerar_video_vibes():
    cookie_header = formatar_cookies_para_header()
    if not cookie_header: 
        return False

    print("🎬 Etapa: Solicitando vídeo na Vibes.ai...")
    url = "https://vibes.ai" 
    
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"duration": 5, "prompt": "Seu prompt de geração"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            dados = response.json()
            video_url = dados.get("video_url") or dados.get("url")
            
            print(f"📥 Baixando vídeo mudo para: {VIDEO_SEM_AUDIO}")
            video_data = requests.get(video_url).content
            with open(VIDEO_SEM_AUDIO, "wb") as f:
                f.write(video_data)
            return True
        print(f"❌ Erro API Vibes ({response.status_code}): {response.text}")
        return False
    except Exception as e:
        print(f"❌ Erro de conexão com Vibes.ai: {e}")
        return False

def adicionar_audio_ao_video():
    print(f"🎵 Misturando {AUDIO_INPUT} com {VIDEO_SEM_AUDIO}...")
    
    # O comando FFmpeg junta o áudio ao vídeo e força o corte em exatos 5s (-shortest)
    comando = [
        "ffmpeg", "-y",
        "-i", VIDEO_SEM_AUDIO,
        "-i", AUDIO_INPUT,
        "-c:v", "copy",       
        "-c:a", "aac",        
        "-map", "0:v:0", 
        "-map", "1:a:0", 
        "-shortest",          
        VIDEO_FINAL
    ]

    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode == 0:
        print(f"🚀 Sucesso absoluto! Vídeo final salvo em: {VIDEO_FINAL}")
    else:
        print(f"❌ Erro FFmpeg na junção: {resultado.stderr}")

async def main():
    # 1. Primeiro cria o áudio gratuito via IA
    audio_criado = await gerar_audio_do_video_gratis()
    
    if audio_criado:
        # 2. Busca o vídeo na API do Vibes.ai
        if gerar_video_vibes():
            # 3. Une os dois arquivos na pasta final
            adicionar_audio_ao_video()

if __name__ == "__main__":
    asyncio.run(main())
