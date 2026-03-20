import gradio as gr

# def greet(name, intensity):
#     return "Hello, " + name + "!" * int(intensity)

def convert_temperature(temperature, direction):
    try:
        temp = float(temperature)

        absolute_zero_c = -273.15
        absolute_zero_f = -459.67

        if direction == "Celsius --> Fahrenheit":
            if temp < absolute_zero_c:
                return "", gr.update(visible=True, value=" ⚠️ Temperature cannot be below absolute zero (-273.15°C).")
            converted = (temp * 9/5) + 32
            return f"<div class='output_result'><span class='result_label'>Result</span><span class='result_value'>{temp}°C is {converted:.2f}°F</span></div>", gr.update(visible=False)
        else:
            if temp < absolute_zero_f:
                return "", gr.update(visible=True, value=" ⚠️ Temperature cannot be below absolute zero (-459.67°F).")
            converted = (temp - 32) * 5/9
            return f"<div class='output_result'><span class='result_label'>Result</span><span class='result_value'>{temp}°F is {converted:.2f}°C</span></div>", gr.update(visible=False)
    except TypeError:
        return "",gr.update(visible=True, value=" ⚠️ Please enter a valid number.")

css = """

.output_result{
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 88px;
    justify-content: center;
    background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
    border: 1px solid #dbe2ea;
    border-left: 5px solid #1f6feb;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(20, 28, 45, 0.08);
    padding: 14px 16px;
    color: #1f2937;
}

.result_label {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #607087;
}

.result_value {
    font-size: 1.3rem;
    font-weight: 800;
    line-height: 1.25;
}
"""


with gr.Blocks(css=css) as demo:
    markdown= gr.Markdown("🌡️ Temperature Converter")
    with gr.Row():
        with gr.Column(scale=2):
            temperature_input = gr.Number(label="Temperature")
            temperature_direction = gr.Radio(label="Conversion Direction", choices=["Celsius --> Fahrenheit", "Fahrenheit --> Celsius"])
            convert_button = gr.Button("Convert")
            error_message = gr.Textbox(label="Error", interactive=False, visible=False)
        
        with gr.Column(scale=1):
            result = gr.HTML()

    callback = {
        "fn": convert_temperature,
        "inputs": [temperature_input, temperature_direction],
        "outputs": [result, error_message]
    }

    convert_button.click(**callback)
    temperature_input.input(**callback)
    temperature_direction.change(**callback)
    

demo.launch(theme=gr.themes.Monochrome(font="sans serif"))