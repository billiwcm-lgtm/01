import os
import json
import asyncio
import subprocess
import requests
import edge_tts

# Captura as variáveis enviadas via JSON ou ambiente
DADOS_RECEBIDOS = os.getenv("DADOS_NOTION_JSON")
COOKIES_JSON = os.getenv("VIBES_COOKIES")

# Estrutura local de pastas temporárias
PASTA_AUDIOS = "audios_gerados"
PASTA_VIDEOS_MUDOS = "videos_mudos"
PASTA_FINAIS = "videos_finais"

for pasta in [PASTA_AUDIOS, PASTA_VIDEOS_MUDOS, PASTA_FINAIS]:
    os.makedirs(pasta, exist_ok=True)

# Definição dos nomes e caminhos dos arquivos
AUDIO_INPUT = os.path.join(PASTA_AUDIOS, "audio_gerado.mp3")
VIDEO_SEM_AUDIO = os.path.join(PASTA_VIDEOS_MUDOS, "video_mudo.mp4")
VIDEO_FINAL = os.path.join(PASTA_FINAIS, "video_final_sincronizado.mp4")

def formatar_cookies_para_header():
    if not COOKIES_JSON:
        print("⚠️ VIBES_COOKIES não configurado. Continuando sem cookies...")
        return ""
    try:
        cookies_list = json.loads(COOKIES_JSON)
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
    except Exception as e:
        print(f"❌ Erro ao decodificar VIBES_COOKIES: {e}")
        return ""

async def pipeline_principal():
    print("🤖 Iniciando Motor de Processamento de Mídia...")

    # Configurações padrão caso rode sem o Notion/Activepieces (teste manual)
    prompt_video = "Avatar falando de forma neutra"
    texto_audio = "Processando integração automática entre GitHub, Vibes e Google Drive."
    tempo_inicio_audio = 0.0
    voz_escolhida = "pt-BR-AntonioNeural"

    if DADOS_RECEBIDOS:
        try:
            dados = json.loads(DADOS_RECEBIDOS)
            prompt_video = dados.get("prompt_video", prompt_video)
            texto_audio = dados.get("texto_audio", texto_audio)
            tempo_inicio_audio = float(dados.get("tempo_inicio_audio", tempo_inicio_audio))
            voz_escolhida = dados.get("voz", voz_escolhida)
            print("✅ Payload de contexto lido com sucesso.")
        except Exception as e:
            print(f"⚠️ Falha ao ler JSON de entrada ({e}). Usando dados padrão.")

    # --- ETAPA 1: GERAR ÁUDIO GRATUITO ---
    print(f"🎙️ Convertendo texto em fala: '{texto_audio}'")
    try:
        communicate = edge_tts.Communicate(texto_audio, voz_escolhida)
        await communicate.save(AUDIO_INPUT)
    except Exception as e:
        print(f"❌ Erro ao gerar áudio: {e}")
        return

    # --- ETAPA 2: REQUISIÇÃO VIBES.AI ---
    cookie_header = formatar_cookies_para_header()
    url_vibes = "https://vibes.ai"
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"duration": 5, "prompt": prompt_video}

    try:
        response = requests.post(url_vibes, json=payload, headers=headers, timeout=10)
        if response.status_code in:
            dados_api = response.json()
            video_url = dados_api.get("video_url") or dados_api.get("url")
            video_data = requests.get(video_url).content
            with open(VIDEO_SEM_AUDIO, "wb") as f:
                f.write(video_data)
            print("📁 Vídeo mudo baixado da Vibes.ai.")
        else:
            raise Exception(f"Status {response.status_code}")
    except Exception as e:
        print(f"⚠️ API Vibes.ai indisponível para o teste ({e}).")
        print("⚙️ Gerando vídeo preto temporário de 5 segundos para fins de teste do áudio...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=5", 
            "-c:v", "libx264", "-pix_fmt", "yuv420p", VIDEO_SEM_AUDIO
        ], capture_output=True)

    # --- ETAPA 3: MIXAGEM E TIMERS COM FFMPEG ---
    delay_ms = int(tempo_inicio_audio * 1000)
    print(f"🎵 Aplicando delay de {delay_ms}ms no áudio e unindo mídias...")

    comando_mixagem = [
        "ffmpeg", "-y",
        "-i", VIDEO_SEM_AUDIO,
        "-i", AUDIO_INPUT,
        "-filter_complex", f"[1:a]adelay={delay_ms}|{delay_ms}[aud]; [0:a][aud]amix=inputs=2:duration=first[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FINAL
    ]

    resultado = subprocess.run(comando_mixagem, capture_output=True, text=True)
    if resultado.returncode == 0:
        print(f"🚀 Vídeo editado com sucesso na pasta: {VIDEO_FINAL}")
    else:
        print(f"❌ Erro no FFmpeg: {resultado.stderr}")

if __name__ == "__main__":
    asyncio.run(pipeline_principal())
