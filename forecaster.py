import json, time, math, tempfile, os
import info, hellmonitor
data = info.load_json_files("json")

async def project(times, decay):
    #this hurts my head

    if len(times) < 2:
        return "n/a"

    # convert half-life (hours) → lambda
    half_life = decay * 3600
    lambda_ = math.log(2) / half_life

    now = times[-1][0]

    S_w = 0
    S_wx = 0
    S_wy = 0
    S_wxx = 0
    S_wxy = 0

    for t, h in times:
        age = now - t
        w = math.exp(-lambda_ * age)

        S_w += w
        S_wx += w * t
        S_wy += w * h
        S_wxx += w * t * t
        S_wxy += w * t * h

    denominator = S_w * S_wxx - S_wx * S_wx

    if denominator == 0:
        return "n/a"

    slope = (S_w * S_wxy - S_wx * S_wy) / denominator

    # Only forecast if health is decreasing
    if slope >= 0:
        return "n/a"

    intercept = (S_wy - slope * S_wx) / S_w

    # Solve for health = 0
    t_zero = -intercept / slope

    # Prevent nonsense past predictions
    if t_zero <= now:
        return "n/a"

    return f"<t:{int(t_zero)}:R>"

async def forecast(area, id):
    with open("forecastlog.json", "r") as f:
        flog = json.load(f)
    times = []
    diffs = []
    if area == "cities":
        name = data.planets.planetRegion[id]
    else:
        name = data.planets.planets[id]
    try:
        for check in flog[area][id]:
            times.append((int(check), flog[area][id][check]))
    except KeyError:
        return f"{name['name'].title()}: item not in log; inactive or bottlenecked by city liberation\n"
    if len(times) <= 1:
        return f"{name['name'].title()}: item in log but no data is available; probably recently started or concluded\n"
    for element in times:
        if times.index(element) == 0:
            continue
        diffs.append((element[0], element[1] - times[times.index(element) - 1][1]))

    total = 0
    healths = []
    for element in diffs:
        total += element[1]
        healths.append(element[1])
    avg = total / len(diffs)

    projection = await project(times, 4)

    print(len(diffs), diffs)
    print(len(times), times)

    # % change in health 1hr, 4hrs, 8hrs
    now = int(times[-1][0])
    current = int(times[-1][1])
    targets = [now - 3600, now - 4 * 3600, now - 8 * 3600]
    stats = []
    for target in targets:
        # find most recent point at or before the target
        candidates = [h for t, h in times if t <= target]
        if candidates and candidates[-1] != 0:
            past = candidates[-1]
            change = 100 - (100 * current / past)
            stats.append(change)
        else:
            stats.append(None)
    formatted = []
    for value in stats:
        if value is None:
            formatted.append(":red_circle: N/A ")
        elif value < 0:
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

    cutoff = int(sp) - 9 * 3600
    for category in flog: # delete anything old/empty
        for item in list(flog[category].keys()):
            for stamp in list(flog[category][item].keys()):
                if int(stamp) < cutoff:
                    del flog[category][item][stamp]
            if not flog[category][item]:
                del flog[category][item]

    tmp_path = "forecastlog.json.tmp"
    with open(tmp_path, "w") as f:
        json.dump(flog, f)
    os.replace(tmp_path, "forecastlog.json")