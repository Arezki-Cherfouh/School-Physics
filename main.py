import os, json, base64
from fastapi import FastAPI
from telethon import TelegramClient
from contextlib import asynccontextmanager
import os, json, base64, requests
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
group_username = os.getenv("GROUP_USERNAME")
client = TelegramClient("session_name", api_id, api_hash)
api_key = os.getenv("IMGBB_API_KEY") 
# CACHE_FILE = "image_cache.json"
GITHUB_TOKEN= os.getenv("GITHUB_TOKEN")
REPO = "Arezki-Cherfouh/School-Physics"
FILE_PATH = "data/image_cache.json"
def get_github_cache():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        return json.loads(content)
    elif r.status_code == 404:
        print("⚠️ Cache file not found. Creating new one...")
        payload = {"message": "Create image cache","content": base64.b64encode(json.dumps([]).encode()).decode(),}
        create = requests.put(url, headers=headers, json=payload)
        if create.status_code in (200, 201):
            print("✅ Created new image_cache.json in GitHub")
        else:
            print("❌ Failed to create cache:", create.text)
        return []
    else:
        print("⚠️ Failed to load cache from GitHub:", r.text)
        return []
def save_github_cache(data):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha", None)
    content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = {"message": "Update image cache","content": content,"sha": sha}
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        print("⚠️ Failed to save cache:", r.text)
    else:
        print("✅ Cache updated in GitHub")
@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.start()
    # if not os.path.exists(CACHE_FILE):
    #     with open(CACHE_FILE, "w") as f:
    #         json.dump([], f)
    yield
    await client.disconnect()
app = FastAPI(lifespan=lifespan)
# def load_cache():
#     try:
#         with open(CACHE_FILE, "r") as f:
#             return json.load(f)
#     except Exception:
#         return []
# def save_cache(data):
#     with open(CACHE_FILE, "w") as f:
#         json.dump(data, f)
def upload_to_imgbb(image_bytes: bytes) -> str:
    if not api_key:
        raise ValueError("IMGBB_API_KEY not set")
    image_b64 = base64.b64encode(image_bytes).decode()
    payload = {"key": api_key,"image": image_b64,"expiration": 15552000}
    response = requests.post("https://api.imgbb.com/1/upload", data=payload)
    response.raise_for_status()
    data = response.json()
    return data["data"]["url"]
def url_exists(url: str) -> bool:
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False
images = get_github_cache()
valid_images = []
for img in images:
    if url_exists(img.get("url", "")):
        valid_images.append(img)
images = valid_images
@app.get("/get-images")
async def get_images():
    # images = get_github_cache()
    valid_images = []
    for img in images:
        if url_exists(img.get("url", "")):
            valid_images.append(img)
    images = valid_images
    async for msg in client.iter_messages(group_username):
        if msg.photo or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/")):
            if any(img["message_id"] == msg.id for img in images):
                continue
            data = await msg.download_media(bytes=True)
            url=upload_to_imgbb(data)
            # encoded = base64.b64encode(data).decode()
            # images.append({"message_id": msg.id,"sender_id": msg.sender_id,"caption": msg.message or "","image_base64": encoded,"url":url})
            images.append({"message_id": msg.id,"sender_id": msg.sender_id,"caption": msg.message or "","url":url})
    save_github_cache(images)
    return {"count": len(images), "images": images}
@app.get("/favicon")
async def favicon():
    if os.path.exists("favicon.png"):
        print("Exists")
        return FileResponse("favicon.png")
    print("404")
    return {"error": "favicon not found"}
@app.get("/", response_class=HTMLResponse)
async def homepage():
    # images = get_github_cache()
    valid_images = []
    for img in images:
        if url_exists(img.get("url", "")):
            valid_images.append(img)
    images = valid_images
    async for msg in client.iter_messages(group_username):
        if msg.photo or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/")):
            if any(img["message_id"] == msg.id for img in images):
                continue
            data = await msg.download_media(bytes=True)
            url = upload_to_imgbb(data)
            images.append({"message_id": msg.id,"sender_id": msg.sender_id,"caption": msg.message or "","url": url})
    save_github_cache(images)
    rows = []
    for img in reversed(images):
        caption_html = f"<div class='caption'>Sender: {img.get('sender_id','')}"
        if img.get("caption"):
            caption_html += f" — {img['caption']}"
        caption_html += "</div>"

        rows.append(f"""
            <div class="card">
              <img src="{img['url']}" alt="image-{img['message_id']}"/>
              {caption_html}
            </div>
        """)
    html = f"""
    <!doctype html>
    <html lang="fr">
        <head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width,initial-scale=1"/>
            <title>Physics Exercises</title>
            <link rel="icon" href="/favicon" type="image/x-icon">
            <style>
                body {{
                    font-family: system-ui, sans-serif;
                    background: #f6f7fb;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                h1 {{
                    margin: 16px 0;
                }}
                .scroll-container {{
                    position: relative;
                    width: 90%;
                    max-width: 90vw;
                    height: 85vh;
                    overflow: hidden;
                    border-radius: 12px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.1);
                    background: white;
                }}
                .scroll-content {{
                    display: flex;
                    overflow-x: auto;
                    height: 100%;
                    scroll-behavior: smooth;
                }}
                .scroll-content::-webkit-scrollbar {{
                    display: none;
                }}
                .card {{
                    flex: 0 0 auto;
                    width: 320px;
                    margin: 12px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    cursor: pointer;
                    transition: 0.2s;
                }}
                .card:hover{{
                    transform: scale(1.05)
                }}
                .card img {{
                    width: 100%;
                    display: block;
                    height: auto;
                }}
                .caption {{
                    padding: 6px 10px;
                    font-size: 14px;
                    color: #333;
                    background: #f0f0f0;
                }}
                .arrow {{
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: rgba(0,0,0,0.6);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    user-select: none;
                    font-size: 22px;
                    transition: background 0.2s;
                    z-index: 10;
                }}
                .arrow:hover {{
                    background: rgba(0,0,0,0.8);
                }}
                .arrow.left {{
                    left: 8px;
                }}
                .arrow.right {{
                    right: 8px;
                }}
                .image-overlay {{
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.85);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.25s ease;
                    z-index: 1000;
                }}
                .image-overlay.active {{
                    opacity: 1;
                    pointer-events: auto;
                }}
                .image-overlay img {{
                    max-width: 90%;
                    max-height: 90%;
                    border-radius: 10px;
                    box-shadow: 0 0 25px rgba(0,0,0,0.6);
                    transition: transform 0.2s ease;
                }}
                .image-overlay.active img:hover {{
                    transform: scale(1.02);
                }}
            </style>
        </head>
        <body>
            <h1>Telegram Gallery</h1>
            <div class="scroll-container">
                <div class="arrow left" onclick="scrollLeftbtn()">◀</div>
                <div class="scroll-content">
                    {''.join(rows) if rows else '<p style="text-align:center;padding:20px;">No images found.</p>'}
                </div>
                <div class="arrow right" onclick="scrollRight()">▶</div>
            </div>
            <script>
                const container = document.querySelector('.scroll-content');
                function scrollLeftbtn() {{
                    container.scrollBy({{ left: -300, behavior: 'smooth' }});
                }}
                function scrollRight() {{
                    container.scrollBy({{ left: 300, behavior: 'smooth' }});
                }}
                document.querySelectorAll('.card img').forEach(img => {{
                    img.addEventListener('click', () => {{
                        let overlay = document.querySelector('.image-overlay');
                        if (!overlay) {{
                            overlay = document.createElement('div');
                            overlay.className = 'image-overlay';
                            overlay.innerHTML = '<img>';
                            document.body.appendChild(overlay);
                            overlay.addEventListener('click', () => overlay.classList.remove('active'));
                            document.addEventListener('keydown', ev => {{
                                if (ev.key === 'Escape') overlay.classList.remove('active');
                            }});
                        }}
                        overlay.querySelector('img').src = img.src;
                        overlay.classList.add('active');
                    }});
                }});
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)