import os
import json
import subprocess
import requests

# Configurações de Ambiente
COOKIES_JSON = os.getenv("VIBES_COOKIES")

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

def gerar_audio_do_video():
    print("🎙️ Etapa: Gerando o áudio do vídeo...")
    # Substitua as linhas abaixo pela lógica real ou comando que gera seu áudio
    # Exemplo gerando um áudio silencioso de 5s caso use alguma ferramenta CLI:
    comando_gerar_audio = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", 
        "-t", "5", AUDIO_INPUT
    ]
    resultado = subprocess.run(comando_gerar_audio, capture_output=True, text=True)
    
    if resultado.returncode == 0 and os.path.exists(AUDIO_INPUT):
        print(f"✅ Áudio gerado com sucesso em: {AUDIO_INPUT}")
        return True
    print(f"❌ Falha ao gerar áudio: {resultado.stderr}")
    return False

def gerar_video_vibes():
    cookie_header = formatar_cookies_para_header()
    if not cookie_header: return False

    print("🎬 Etapa: Solicitando vídeo na Vibes.ai...")
    url = "https://vibes.ai" # Ajuste se houver URL específica
    
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"duration": 5, "prompt": "Seu prompt de geração"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in:
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
        print(f"❌ Erro de conexão: {e}")
        return False

def adicionar_audio_ao_video():
    print(f"🎵 Misturando {AUDIO_INPUT} com {VIDEO_SEM_AUDIO}...")
    
    comando = [
        "ffmpeg", "-y",
        "-i", VIDEO_SEM_AUDIO,
        "-i", AUDIO_INPUT,
        "-c:v", "copy",       # Rápido: não re-codifica o vídeo
        "-c:a", "aac",        # Converte o áudio para formato compatível
        "-map", "0:v:0", 
        "-map", "1:a:0", 
        "-shortest",          # Garante o corte cravado em 5 segundos
        VIDEO_FINAL
    ]

    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode == 0:
        print(f"🚀 Sucesso absoluto! Vídeo final salvo em: {VIDEO_FINAL}")
    else:
        print(f"❌ Erro FFmpeg na junção: {resultado.stderr}")

if __name__ == "__main__":
    # Executa o fluxo sequencial criando os arquivos em suas respectivas pastas
    if gerar_audio_do_video():
        if gerar_video_vibes():
            adicionar_audio_ao_video()
