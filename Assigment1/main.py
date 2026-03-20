import gradio as gr
import pandas as pd
import httpx

def fetch_species(conservation_status="All"):
    result = httpx.get("http://127.0.0.1:8000/species/")
    
    result.raise_for_status()  # Ensure we raise an error for bad responses
    data = result.json()

    df = pd.DataFrame(data, columns=["id", "name", "scientific_name","family","conservation_status","wingspan_cm"])
    if conservation_status != "All":
        return df[df["conservation_status"] == conservation_status]
    
    return df

def add_species(name, scientific_name, family, conservation_status, wingspan_cm):
    payload = {
        "name": name,
        "scientific_name": scientific_name,
        "family": family,
        "conservation_status": conservation_status,
        "wingspan_cm": wingspan_cm
    }
    response = httpx.post("http://127.0.0.1:8000/species/", json=payload)
    response.raise_for_status()

    return f"Species '{name}' added successfully!"

def get_species_dropdown_choices():
    species_df = fetch_species("All")
    if species_df.empty:
        return []
    return [(f"{row['name']} (id={row['id']})", int(row["id"])) for _, row in species_df.iterrows()]

def fetch_birds():
    result = httpx.get("http://127.0.0.1:8000/birds/")
    result.raise_for_status()
    data = result.json()

    df_bird = pd.DataFrame(data, columns=["id", "nickname", "ring_code", "age", "species_id"])

    # Replace raw species IDs with readable species names for display.
    species_df = fetch_species("All")[["id", "name"]].rename(columns={"id": "species_id", "name": "species"})
    merged = df_bird.merge(species_df, how="left", on="species_id")
    merged["species"] = merged["species"].fillna("Unknown")

    return merged[["id", "nickname", "ring_code", "age", "species"]]


def add_bird(nickname, ring_code, age, species_id):
    if species_id is None:
        return "Please select a species.", fetch_birds()

    payload = {
        "nickname": nickname,
        "ring_code": ring_code,
        "age": int(age),
        "species_id": int(species_id)
    }

    try:
        response = httpx.post("http://127.0.0.1:8000/birds/", json=payload)
        response.raise_for_status()
        return f"Bird '{nickname}' added successfully!", fetch_birds()
    except httpx.HTTPStatusError as exc:
        detail = "Unknown validation error"
        try:
            body = exc.response.json()
            if isinstance(body.get("detail"), list) and body["detail"]:
                detail = "; ".join(item.get("msg", str(item)) for item in body["detail"])
            elif "detail" in body:
                detail = str(body["detail"])
        except Exception:
            pass
        return f"Could not add bird: {detail}", fetch_birds()

def fetch_sightings(observer_name=""):
    result = httpx.get("http://127.0.0.1:8000/birdspottings/")
    result.raise_for_status()
    data = result.json()

    df_sighting = pd.DataFrame(data, columns=["bird_id", "bird", "spotted_at", "location", "observer_name", "notes"])
    df_sighting["bird"] = df_sighting["bird"].apply(
        lambda b: b.get("nickname") if isinstance(b, dict) else "Unknown"
    )
    if observer_name:
        df_sighting = df_sighting[
            df_sighting["observer_name"].str.contains(observer_name, case=False, na=False)
        ]

    return df_sighting[["bird", "spotted_at", "location", "observer_name", "notes"]]

def add_sighting(bird_id, spotted_at, location, observer_name, notes):
    if bird_id is None:
        return "Could not add sighting: please select a bird.", gr.update()
    if not spotted_at or not str(spotted_at).strip():
        return "Could not add sighting: spotted_at is required (ISO 8601, e.g. 2026-03-20T10:30:00Z).", gr.update()
    if not location or not str(location).strip():
        return "Could not add sighting: location is required.", gr.update()
    if not observer_name or not str(observer_name).strip():
        return "Could not add sighting: observer_name is required.", gr.update()

    payload = {
        "bird_id": int(bird_id),
        "spotted_at": str(spotted_at).strip(),
        "location": str(location).strip(),
        "observer_name": str(observer_name).strip(),
        "notes": str(notes).strip() if notes is not None else None
    }

    try:
        response = httpx.post("http://127.0.0.1:8000/birdspottings/", json=payload)
        response.raise_for_status()
        return f"Sighting added successfully!", fetch_sightings()
    except httpx.HTTPStatusError as exc:
        detail = "Unknown validation error"
        try:
            body = exc.response.json()
            if isinstance(body.get("detail"), list) and body["detail"]:
                detail = "; ".join(item.get("msg", str(item)) for item in body["detail"])
            elif "detail" in body:
                detail = str(body["detail"])
        except Exception:
            pass
        return f"Could not add sighting: {detail}", gr.update()

def get_bird_dropdown_choices():
    birds_df = fetch_birds()
    if birds_df.empty:
        return []

    return [
        (f"{row['nickname']} [{row['ring_code']}]", int(row["id"]))
        for _, row in birds_df.iterrows()
    ]


def refresh_bird_dropdown():
    choices = get_bird_dropdown_choices()
    default_value = choices[0][1] if choices else None
    return gr.update(choices=choices, value=default_value)


# Make sure this matches your data structure 
conservation_statuses = [
    "Least Concern",
    "Near Threatened",
    "Vulnerable",
    "Endangered",
    "Critically Endangered",
    "Extinct in the Wild",
    "Extinct"
]

with gr.Blocks(theme=gr.themes.Soft(primary_hue='blue')) as demo:

    info_markdown = gr.Markdown("🐦Bird Viewer")
    description = gr.Markdown("Live data from the BirdsAPI at: http://127.0.0.1:8000")

    with gr.Tab("Species"):
        with gr.Row():
            conservation_filter_dropdown = gr.Dropdown(label="Filter by Conservation Status", choices=["All"] + conservation_statuses,value="All", scale=3)
            refresh_button = gr.Button("🔄 Refresh", scale=1)
        with gr.Row():
            data = gr.Dataframe(label="Species", value=fetch_species(), interactive=False)
            conservation_filter_dropdown.change(fn=fetch_species, inputs=conservation_filter_dropdown, outputs=data)
            refresh_button.click(fn=fetch_species, inputs=conservation_filter_dropdown, outputs=data)
        
        with gr.Row():
            with gr.Accordion(label="Add new species", open=True):
                with gr.Row():
                    name_input = gr.Textbox(label="Name",placeholder="Example: Eagle")
                    scientific_name_input = gr.Textbox(label="Scientific Name", placeholder="Example: Aquila chrysaetos")
                with gr.Row():
                    family_input = gr.Textbox(label="Family", placeholder="Example: Falconidae")
                    conservation_status_input = gr.Dropdown(label="Conservation Status", choices=conservation_statuses,interactive=True)
                    wingspan_input = gr.Slider(label="Wingspan (cm)",minimum=5.5,maximum=370,step=1)
                add_button = gr.Button("Add Species")
                add_button.click(fn=add_species, inputs=[name_input, scientific_name_input, family_input, conservation_status_input, wingspan_input], outputs=[])
                    


    with gr.Tab("Birds"):
       
       with gr.Row():
            refresh_button = gr.Button("🔄 Refresh", scale=1)
       with gr.Row():
            data = gr.Dataframe(label="Birds", value=fetch_birds(), interactive=False)
            refresh_button.click(fn=fetch_birds, outputs=data)
       with gr.Row():
            with gr.Accordion(label="Add new bird", open=True):
                with gr.Row():
                    name_input = gr.Textbox(label="Nickname",placeholder="Example: Skipper")
                    ring_code_input = gr.Textbox(label="Ring Code", placeholder="Example: AB-12345")
                with gr.Row():
                    age_input = gr.Number(label="Age", minimum=0, maximum=120, step=1, value=1)
                    species_input = gr.Dropdown(label="Species", choices=get_species_dropdown_choices(), type="value", interactive=True)
                add_button = gr.Button("Add Bird")
                bird_add_status = gr.Markdown()
                add_button.click(fn=add_bird, inputs=[name_input, ring_code_input, age_input, species_input], outputs=[bird_add_status, data])
             


    with gr.Tab("Sightings"):
        
        with gr.Row():
            observed_name_filter = gr.Textbox(label="Filter by observed name",placeholder="Example: Jane",scale=3)
            refresh_button = gr.Button("🔄 Refresh", scale=1)
        with gr.Row():
            data = gr.Dataframe(label="Sightings", value=fetch_sightings(), interactive=False)
            observed_name_filter.change(fn=fetch_sightings, inputs=observed_name_filter, outputs=data)
            refresh_button.click(fn=fetch_sightings, inputs=observed_name_filter, outputs=data)
        with gr.Row():
            with gr.Accordion(label="Add new sighting", open=True):
                with gr.Row():
                    bird_input = gr.Dropdown(label="Bird", choices=get_bird_dropdown_choices(), type="value", interactive=True)
                    refresh_button_birds = gr.Button("🔄 Refresh Bird list", scale=1)
                    refresh_button_birds.click(fn=refresh_bird_dropdown, outputs=bird_input)
                with gr.Row():
                    spotted_at_input = gr.Textbox(label="Spotted At", placeholder="Example: 2024-06-01T14:30:00Z")
                    location_input = gr.Textbox(label="Location", placeholder="Example: Central Park, NY")
                with gr.Row():
                    observer_name_input = gr.Textbox(label="Observer Name", placeholder="Example: Jane Doe")
                    notes_input = gr.Textbox(label="Notes", placeholder="Example: Saw the bird near the lake.")
                add_button = gr.Button("Add Sighting")
                sighting_add_status = gr.Markdown()
                add_button.click(fn=add_sighting, inputs=[bird_input, spotted_at_input, location_input, observer_name_input, notes_input], outputs=[sighting_add_status, data])
                refresh_button_birds.click(fn=refresh_bird_dropdown, outputs=bird_input)
    



demo.launch()