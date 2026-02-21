import json, time
import info, hellmonitor
data = info.load_json_files("json")

async def forecast(area, name):
    with open("forecastlog.json", "r") as f:
        flog = json.load(f)
    times = []
    diffs = []
    try:
        for check in flog[area][name]:
            times.append((check, flog[area][name][check]))
    except KeyError:
        return "no logged data; planet inactive or bottlenecked by city liberation"
    if len(times) <= 1:
        return "no forecast"
    for element in times:
        if times.index(element) == 0:
            continue
        diffs.append((element[0], element[1] - times[times.index(element) - 1][1]))
    if area == "cities":
        name = data.planets.planetRegion[name]
    else:
        name = data.planets.planets[name]

    total = 0
    healths = []
    for element in diffs:
        total += element[1]
        healths.append(element[1])
    avg = total / len(diffs)

    projection = "n/a"
    if avg < 0:
        projection = times[-1][1] / (avg * -1)
        projection *= 600
        projection += int(times[-1][0])
        projection = f"<t:{int(projection)}:R>"

    return f"{str.title(name["name"])}: {round(avg * -6, 2)} dph, forecast {projection}"

async def search_and_fcast(name):
    name = name.upper()
    for element in data.planets.planets:
        if data.planets.planets[element]["name"].upper() == name:
            return await forecast("planets", element)
    for element in data.planets.planetRegion:
        if data.planets.planetRegion[element]["name"].upper() == name:
            return await forecast("cities", element)
    return "planet/city not found"

async def updateLog():
    print("updating forecast log at ", time.time())
    with open("forecastlog.json", "r") as f:
        flog = json.load(f)
    planets, discard = await hellmonitor.fetch("/api/v1/planets", False)
    sp = str(int(time.time()))
    for planet in planets:
        if type(planet["health"]) == int:
            if planet["health"] != planet["maxHealth"]:
                planet_id = str(planet["index"])
                flog["planets"].setdefault(planet_id, {})
                flog["planets"][planet_id][sp] = planet["health"]
        else:
            print(planet["health"])

        if len(planet["regions"]) > 0:
            for city in planet["regions"]:
                if city["health"] != city["maxHealth"] and city["health"] is not None:
                    city_id = str(city["hash"])
                    flog["cities"].setdefault(city_id, {})
                    flog["cities"][city_id][sp] = city["health"]

    for category in flog:
        for item in flog[category]:
            for stamp in list(flog[category][item].keys()):
                if int(stamp) < int(sp) - 8 * 3600:
                    del flog[category][item][stamp]

    with open("forecastlog.json", "w") as f:
        json.dump(flog, f)