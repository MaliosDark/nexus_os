import os
import uuid
import base64
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import base64

# Configuration
UPLOAD_FOLDER = './uploads'
ASCII_FOLDER = './ascii_output'
PUBLISHED_FOLDER = './ascii_published'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ASCII_FOLDER, exist_ok=True)
os.makedirs(PUBLISHED_FOLDER, exist_ok=True)

WATERMARK_TEXT = "Nexus-Ereb.us"
URL_STABLE_DIFFUSION = "http://127.0.0.1:7860"  # Change if necessary
#MODEL_NAME = "pepe_frog SDXL.safetensors"  # Nombre de tu modelo personalizado
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 

def generate_image_from_text(prompt: str, output_path: str):
    """
    Genera una imagen de alta calidad a partir de un prompt de texto usando un modelo Stable Diffusion 
    con parámetros avanzados y añade una marca de agua automáticamente.
    """
    payload = {
        "prompt": prompt,
        "steps": 50,  # Número de pasos de generación
        "sd_model_checkpoint": "Real.safetensors",  # Modelo personalizado
        "seed": -1,
        "sampler_name": "DPM++ 2M",  # Sampler especificado
        "scheduler": "Karras",  # Tipo de programación para el sampler
        "cfg_scale": 7  # Control de escala CFG para ajuste de precisión
    }
    
    try:
        response = requests.post(
            url=f"{URL_STABLE_DIFFUSION}/sdapi/v1/txt2img",
            json=payload
        )
        response.raise_for_status()
        r = response.json()
        image_base64 = r["images"][0]
        image_data = base64.b64decode(image_base64)
        
        # Guardar la imagen generada
        temp_path = f"{output_path}.tmp"  # Archivo temporal
        with open(temp_path, "wb") as f:
            f.write(image_data)
        print(f"Imagen generada y guardada temporalmente en {temp_path}")
        
        # Añadir marca de agua
        add_watermark(temp_path, output_path)
        print(f"Imagen con marca de agua guardada en {output_path}")
        
        # Eliminar el archivo temporal
        os.remove(temp_path)
    except Exception as e:
        raise RuntimeError(f"Error al generar la imagen desde el texto: {e}")



def add_watermark(image_path, output_path):
    """Adds a watermark to an image."""
    image = Image.open(image_path).convert("RGBA")
    watermark = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)  # Ensure this font is installed
    except OSError:
        raise RuntimeError("Font not found. Ensure 'DejaVuSans.ttf' is available or specify another font.")

    # Use `textbbox` to calculate text dimensions
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Calculate the watermark position at the bottom-right corner with padding
    position = (image.size[0] - text_width - 10, image.size[1] - text_height - 10)
    draw.text(position, WATERMARK_TEXT, fill=(255, 255, 255, 128), font=font)

    # Merge the watermark with the original image
    combined = Image.alpha_composite(image, watermark)
    combined.convert("RGB").save(output_path)

def generate_ascii_image(input_path, output_path, num_cols=100, scale=2, bg_color="black", char_set="@%#*+=-:. ", color_mode="original"):
    num_chars = len(char_set)
    bg_code = (255, 255, 255) if bg_color == "white" else (0, 0, 0)

    image = Image.open(input_path).convert('RGB')
    width, height = image.size
    cell_width = width / num_cols
    cell_height = scale * cell_width
    num_rows = int(height / cell_height)

    char_width, char_height = 6, 12
    out_width = char_width * num_cols
    out_height = char_height * num_rows
    out_image = Image.new("RGB", (out_width, out_height), bg_code)
    draw = ImageDraw.Draw(out_image)

    for i in range(num_rows):
        for j in range(num_cols):
            crop = image.crop(
                (j * cell_width, i * cell_height, (j + 1) * cell_width, (i + 1) * cell_height)
            )
            avg_color = tuple(np.array(crop).mean(axis=(0, 1)).astype(int))
            intensity = np.mean(avg_color)
            char = char_set[min(int((intensity / 255) * num_chars), num_chars - 1)]
            fill_color = avg_color if color_mode == "original" else (255, 0, 0)
            draw.text((j * char_width, i * char_height), char, fill=fill_color)

    # Añadir marca de agua
    watermark = ImageDraw.Draw(out_image)
    try:
        font = ImageFont.truetype(FONT_PATH, 20)  # Ruta de la fuente
    except OSError:
        raise RuntimeError("Font not found. Please ensure the font path is correct.")

    # Usa `getbbox()` para calcular el tamaño del texto
    bbox = font.getbbox(WATERMARK_TEXT)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Posición para la marca de agua
    position = (out_image.size[0] - text_width - 10, out_image.size[1] - text_height - 10)
    watermark.text(position, WATERMARK_TEXT, fill=(255, 255, 255, 128), font=font)

    # Guardar la imagen final con ASCII y watermark
    out_image.save(output_path)


def optimize_for_twitter(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            # Cambia ANTIALIAS a Resampling.LANCZOS
            img = img.resize((1200, 675), Image.Resampling.LANCZOS)  # Tamaño recomendado para Twitter
            img.save(output_path, format="PNG", optimize=True)
            print(f"[LOG] Image optimized and saved at {output_path}")
    except Exception as e:
        print(f"[ERROR] Error al optimizar la imagen para Twitter: {e}")
        raise

def generate_image_and_ascii_base64(prompt: str):
    """Generates an image from text, adds watermark, converts to ASCII art, and returns Base64-encoded images."""
    # Ruta y nombres de archivo
    image_filename = f"{uuid.uuid4()}.png"
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)

    # Generar imagen desde texto
    generate_image_from_text(prompt, image_path)

    # Agregar marca de agua a la imagen generada
    watermarked_image_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_{image_filename}")
    add_watermark(image_path, watermarked_image_path)

    # Optimizar para Twitter
    twitter_image_path = os.path.join(PUBLISHED_FOLDER, f"twitter_{image_filename}")
    optimize_for_twitter(watermarked_image_path, twitter_image_path)

    # Agregar marca de agua a la imagen optimizada para Twitter
    twitter_watermarked_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_twitter_{image_filename}")
    add_watermark(twitter_image_path, twitter_watermarked_path)

    # Generar arte ASCII desde la imagen con marca de agua
    ascii_image_filename = f"ascii_{image_filename}"
    ascii_image_path = os.path.join(ASCII_FOLDER, ascii_image_filename)
    generate_ascii_image(
        input_path=watermarked_image_path,  # Usar la imagen con marca de agua
        output_path=ascii_image_path,
        num_cols=100,
        scale=2,
        bg_color="black",
        char_set="@%#*+=-:. ",
        color_mode="original"
    )

    # Agregar marca de agua al arte ASCII
    watermarked_ascii_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_{ascii_image_filename}")
    add_watermark(ascii_image_path, watermarked_ascii_path)

    # Convertir las imágenes generadas a Base64
    def encode_image_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    # Retornar imágenes en Base64
    return f"data:image/png;base64,{encode_image_to_base64(image_path)}"

def generate_image_and_ascii(prompt: str):
    """Generates an image from text, adds watermark, converts to ASCII art, and prepares for Twitter."""
    # Ruta y nombres de archivo
    image_filename = f"{uuid.uuid4()}.png"
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)

    # Generar imagen desde texto
    generate_image_from_text(prompt, image_path)

    # Agregar marca de agua a la imagen generada
    watermarked_image_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_{image_filename}")
    add_watermark(image_path, watermarked_image_path)

    # Optimizar para Twitter
    twitter_image_path = os.path.join(PUBLISHED_FOLDER, f"twitter_{image_filename}")
    optimize_for_twitter(watermarked_image_path, twitter_image_path)

    # Agregar marca de agua a la imagen optimizada para Twitter
    twitter_watermarked_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_twitter_{image_filename}")
    add_watermark(twitter_image_path, twitter_watermarked_path)

    # Generar arte ASCII desde la imagen con marca de agua
    ascii_image_filename = f"ascii_{image_filename}"
    ascii_image_path = os.path.join(ASCII_FOLDER, ascii_image_filename)
    generate_ascii_image(
        input_path=watermarked_image_path,  # Usar la imagen con marca de agua
        output_path=ascii_image_path,
        num_cols=100,
        scale=2,
        bg_color="black",
        char_set="@%#*+=-:. ",
        color_mode="original"
    )

    # Agregar marca de agua al arte ASCII
    watermarked_ascii_path = os.path.join(PUBLISHED_FOLDER, f"watermarked_{ascii_image_filename}")
    add_watermark(ascii_image_path, watermarked_ascii_path)

    # Retornar rutas de los archivos generados
    return {
        "original_image": image_path,
        "watermarked_image": watermarked_image_path,
        "twitter_image": twitter_watermarked_path,  # Cambiado a la imagen con watermark
        "ascii_image": ascii_image_path,
        "watermarked_ascii_image": watermarked_ascii_path
    }


def generate_ascii_video(input_path, output_path, num_cols=100, scale=1, bg_color="black",
                         char_set="@%#*+=-:. ", fps=0, overlay_ratio=0.2):
    """
    Convierte un video o GIF a un video ASCII animado.
    """
    if bg_color == "white":
        bg_code = (255, 255, 255)
    else:
        bg_code = (0, 0, 0)

    cap = cv2.VideoCapture(input_path)
    if fps == 0:
        fps = int(cap.get(cv2.CAP_PROP_FPS))

    CHAR_LIST = char_set
    num_chars = len(CHAR_LIST)

    # Configurar el escritor de video
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cell_width = width / num_cols
    cell_height = 2 * cell_width
    num_rows = int(height / cell_height)
    char_width, char_height = 6, 12
    out_width = char_width * num_cols
    out_height = char_height * num_rows

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

    font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", size=int(10 * scale))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        out_image = Image.new("RGB", (out_width, out_height), bg_code)
        draw = ImageDraw.Draw(out_image)

        for i in range(num_rows):
            for j in range(num_cols):
                crop = image.crop((
                    int(j * cell_width),
                    int(i * cell_height),
                    int(min((j + 1) * cell_width, width)),
                    int(min((i + 1) * cell_height, height)),
                ))
                avg_color = tuple(np.array(crop).mean(axis=(0, 1)).astype(int))
                intensity = np.mean(avg_color)
                char_index = max(0, min(int((intensity / 255) * num_chars), num_chars - 1))
                char = CHAR_LIST[char_index]
                fill_color = avg_color
                draw.text((j * char_width, i * char_height), char, fill=fill_color, font=font)

        out.write(np.array(out_image))

    cap.release()
    out.release()