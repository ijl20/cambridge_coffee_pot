
POUR_TEST_SECONDS = 15

def pour_test(time_buffer):
    now = time_buffer.get(0)["ts"]
    print("now={}".format(now))
    stats = []
    current_offset = 0

    for i in range(POUR_TEST_SECONDS):
        # get one-second median
        median, next_offset, duration, sample_count = time_buffer.median(current_offset, 1)
        dev, next_offset, duration, sample_count = time_buffer.deviation(current_offset, 1, median)
        current_offset = next_offset
        stats_value = { "med": median, "dev": dev, "count": sample_count }
        #print(i,stats_value)
        stats.append(stats_value)
    #print(stats)

    # COFFEE_POURED == False if current 1 second weight not stable
    if stats[0] is None:
        print("no stats now")
        return None

    if stats[0]["dev"] is None:
        print("no deviation stats now")
        return None

    if stats[0]["dev"] > 30:
        print("not stable now")
        return None

    push_detected = False

    # look back 15 seconds and see if push detected AND stable prior value was 100.500g higher than latest stable value
    for i in range(1, POUR_TEST_SECONDS):

        # skip if we have no stats for current period
        if stats[i] is None or stats[i]["med"] is None or stats[i]["dev"] is None or stats[i]["count"] is None:
            continue

        # check for push
        if stats[i]["med"] > stats[0]["med"] + 2000 and stats[i]["count"] > 4:
            push_detected = True
            print("push detected at {}".format(i))
            continue

        # check for higher level of coffee before push
        med_delta = stats[i]["med"] - stats[0]["med"]

        if push_detected and stats[i]["dev"] < 30 and med_delta > 100 and med_delta < 500:
            print(stats)
            print("EVENT POURED {:.1f} from {} at {}".format( med_delta, i, now))
            e.put(now, "EVENT_POURED")
            return "EVENT_POURED"

    return None

def process_sample(ts,value):
    t.put(ts,value)
    pour_test(t)

from classes.time_buffer import TimeBuffer

from classes.time_buffer import StatsBuffer

# stats
s = StatsBuffer(size=30, duration=1)

# samples
t = TimeBuffer(size=300, stats_buffer=s)

# events
e = TimeBuffer(size=10)

# replay

r = TimeBuffer(1000)

r.load('../data/2019-11-22_readings.csv')

r.play(process_sample, realtime=True)

print("\n Events")

for i in range(e.size):
    ev = e.get(i)
    if not ev is None:
        print(ev)

