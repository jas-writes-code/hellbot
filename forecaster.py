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
        return "item not in log; inactive or bottlenecked by city liberation"
    if len(times) <= 1:
        return "item in log but no data is available; likely concluded but not yet deleted"
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

    # % change in health 1hr, 4hrs, 8hrs
    hrstat = 100 - (100 * times[-1][1] / times[int(7 * len(times) / 8)][1])
    hrhrstat = 100 - (100 * times[-1][1] / times[int(len(times) / 2)][1])
    hrhrhrstat = 100 - (100 * times[-1][1] / times[0][1])
    stats = [hrstat, hrhrstat, hrhrhrstat]
    formatted = []
    for value in stats:
        if value < 0:
            formatted.append(f":small_red_triangle_down: {value:.2f}% ")
        elif value > 0:
            formatted.append(f":small_red_triangle: {value:.2f}% ")
        else:
            formatted.append(f":red_circle: {value:.2f}% ")
    hrstat, hrhrstat, hrhrhrstat = formatted

    recent = round((int(time.time()) - int(times[-1][0])) / 60, 2)
    content = f"{str.title(name['name'])}: {round(avg * -6, 2)}dph, est {projection}, {recent}min(s)\n"
    content += f"1hr {hrstat} 4hr {hrhrstat} 8hr {hrhrhrstat}\n"
    return content

async def search_and_fcast(name):
    name = name.upper()
    for element in data.planets.planets:
        if data.planets.planets[element]["name"].upper() == name:
            return await forecast("planets", element)
    for element in data.planets.planetRegion:
        if data.planets.planetRegion[element]["name"].upper() == name:
            return await forecast("cities", element)
    return "planet/city not found"

async def fcast_all():
    with open("forecastlog.json", "r") as f:
        flog = json.load(f)
    content = ""
    for area in flog:
        for name in flog[area]:
            content += f"> {await forecast(area, name)}\n"
    return content

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

    cutoff = int(sp) - 8 * 3600
    for category in flog: # delete anything old/empty
        for item in list(flog[category].keys()):
            for stamp in list(flog[category][item].keys()):
                if int(stamp) < cutoff:
                    del flog[category][item][stamp]
            if not flog[category][item]:
                del flog[category][item]

    with open("forecastlog.json", "w") as f:
        json.dump(flog, f)