import gradio as gr
import pandas as pd
from PIL import Image, ImageFilter

# Attempt to import machine learning libraries
try:
    from transformers import pipeline
    # Bonus 2: Using EfficientNet instead of ResNet or ViT for better accuracy/efficiency
    # Note: Requires 'pip install timm'
    classifier = pipeline("image-classification", model="google/efficientnet-b0")
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

def convert_to_grayscale(img):
    """Converts an uploaded PIL image to grayscale."""
    if img is None:
        return None
    return img.convert("L")

def apply_edge_detection(img):
    """Bonus 1: Applies edge detection using PIL."""
    if img is None:
        return None
    # Convert to grayscale first for better edge detection results
    gray_img = img.convert("L")
    return gray_img.filter(ImageFilter.FIND_EDGES)

def extract_image_details(img):
    """Extracts width, height, format, and mode from the image."""
    if img is None:
        return pd.DataFrame()
    
    details = {
        "Property": ["Width (pixels)", "Height (pixels)", "Format", "Color Mode"],
        "Value": [img.width, img.height, img.format or "Unknown (Memory)", img.mode]
    }
    return pd.DataFrame(details)

def recognize_objects(img):
    """Bonus 2: Uses a pre-trained EfficientNet model to classify the main object."""
    if img is None:
        return {"Please upload an image first": 1.0}
    if not HAS_TRANSFORMERS:
        return {"Error: 'transformers', 'torch', or 'timm' library not installed.": 1.0}
    
    try:
        predictions = classifier(img)
        return {pred['label']: pred['score'] for pred in predictions}
    except Exception as e:
        return {f"Error processing image: {str(e)}": 1.0}


# --- Gradio UI Layout ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue='blue')) as demo:
    
    gr.Markdown("## 🖼️ Advanced Image Processing Studio")
    gr.Markdown("Upload an image or use your webcam to process it.")

    # Task 1 & Bonus 1: Filters (Grayscale & Edge Detection)
    with gr.Tab("Image Filters"):
        with gr.Row():
            with gr.Column():
                # Bonus 3: sources=["upload", "webcam"] allows live camera input
                filter_input = gr.Image(sources=["upload", "webcam"], type="pil", label="Input Image")
                with gr.Row():
                    gray_button = gr.Button("Convert to Grayscale", variant="primary")
                    edge_button = gr.Button("Detect Edges", variant="secondary")
            with gr.Column():
                filter_output = gr.Image(type="pil", label="Result", interactive=False)
                
        gray_button.click(fn=convert_to_grayscale, inputs=filter_input, outputs=filter_output)
        edge_button.click(fn=apply_edge_detection, inputs=filter_input, outputs=filter_output)

    # Task 2: Image Details
    with gr.Tab("Image Details"):
        with gr.Row():
            with gr.Column():
                details_input = gr.Image(sources=["upload", "webcam"], type="pil", label="Input Image")
                details_button = gr.Button("Extract Details", variant="primary")
            with gr.Column():
                details_output = gr.Dataframe(label="Image Properties", interactive=False)
                
        details_button.click(fn=extract_image_details, inputs=details_input, outputs=details_output)

    # Task 3 & Bonus 2: Object Recognition (EfficientNet)
    with gr.Tab("Object Recognition"):
        with gr.Row():
            with gr.Column():
                obj_input = gr.Image(sources=["upload", "webcam"], type="pil", label="Input Image")
                obj_button = gr.Button("Recognize Objects", variant="primary")
                if not HAS_TRANSFORMERS:
                    gr.Markdown("*⚠️ Note: You need to install `transformers`, `torch`, and `timm` via pip for this tab to work.*")
            with gr.Column():
                obj_output = gr.Label(num_top_classes=5, label="Top 5 Predictions")
                
        obj_button.click(fn=recognize_objects, inputs=obj_input, outputs=obj_output)

if __name__ == "__main__":
    demo.launch()