import os
import subprocess
import requests

# Em vez de colar o texto cru, o GitHub Actions passará a string JSON do seu arquivo de cookies
COOKIES_JSON = os.getenv("VIBES_COOKIES")
AUDIO_INPUT = "audio_padrao.mp3"  
VIDEO_SEM_AUDIO = "video_mudo.mp4"
VIDEO_FINAL = "video_com_audio.mp4"

def formatar_cookies_para_header():
    """Converte o formato JSON exportado do navegador em uma string para o Header HTTP"""
    import json
    try:
        cookies_list = json.loads(COOKIES_JSON)
        # Junta os cookies no formato "nome=valor; nome2=valor2"
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
        return cookie_string
    except Exception as e:
        print(f"❌ Erro ao processar o formato dos cookies: {e}")
        return ""

def gerar_video_vibes():
    cookie_header = formatar_cookies_para_header()
    if not cookie_header:
        return False

    print("🎬 Solicitando geração de vídeo na Vibes.ai...")
    
    # Endpoint da API (Substitua pela URL de criação de vídeos da plataforma se for diferente)
    url = "https://vibes.ai"  
    
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "duration": 5,
        "prompt": "Coloque o comando ou descrição do seu vídeo aqui",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            # Ajuste a chave dependendo de como a API do Vibes retorna o link (ex: 'url', 'video_url', 'download_link')
            dados = response.json()
            video_url = dados.get("video_url") or dados.get("url")
            
            if not video_url:
                print(f"❌ Resposta da API não continha a URL do vídeo. Resposta completa: {dados}")
                return False

            print(f"📥 Baixando vídeo gerado: {video_url}")
            video_data = requests.get(video_url).content
            with open(VIDEO_SEM_AUDIO, "wb") as f:
                f.write(video_data)
            return True
        else:
            print(f"❌ Erro na API da Vibes (Status {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão com a API: {e}")
        return False

def adicionar_audio():
    print("🎵 Juntando áudio ao vídeo de 5 segundos...")
    
    comando = [
        "ffmpeg", "-y",
        "-i", VIDEO_SEM_AUDIO,
        "-i", AUDIO_INPUT,
        "-c:v", "copy",       # Não re-codifica o vídeo (processo instantâneo)
        "-c:a", "aac",        # Codifica o áudio para máxima compatibilidade
        "-map", "0:v:0",      # Mapeia o canal de vídeo da primeira entrada
        "-map", "1:a:0",      # Mapeia o canal de áudio da segunda entrada
        "-shortest",          # Trava a duração no menor arquivo (garante os 5s)
        VIDEO_FINAL
    ]

    resultado = subprocess.run(comando, capture_output=True, text=True)

    if resultado.returncode == 0:
        print(f"✅ Vídeo editado com sucesso: {VIDEO_FINAL}")
    else:
        print(f"❌ Erro no FFmpeg: {resultado.stderr}")

if __name__ == "__main__":
    if gerar_video_vibes():
        adicionar_audio()
