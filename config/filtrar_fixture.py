import json

with open("respaldo_ok.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

permitidos = {
    "champinones.usuario",
    "champinones.miembrovip",
    "champinones.evento",
    "champinones.eventosector",
    "champinones.boleto",
    "champinones.cierrecaja",
    "champinones.aperturacaja",
    "champinones.recarga",
}

filtrados = [x for x in datos if x["model"] in permitidos]

with open("champinones_only.json", "w", encoding="utf-8") as f:
    json.dump(filtrados, f, ensure_ascii=False)

print("Registros exportados:", len(filtrados))