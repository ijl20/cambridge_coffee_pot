
POUR_TEST_SECONDS = 15

def pour_test(sample_buffer, stats_buffer):

    now = sample_buffer.get(0)["ts"]

    # get latest 1-second median and deviation
    current_median, offset, duration, sample_count = sample_buffer.median(0,1)

    current_deviation, offset, duration, sample_count = sample_buffer.deviation(0,1,current_median)

    # COFFEE_POURED == False if current 1 second weight not stable
    if ( current_median is None or
         offset is None or
         duration is None or
         sample_count is None or
         current_deviation is None ):
        print("{} no stats now".format(now))
        return None

    if current_deviation > 30:
        print("{} deviation not stable = {}".format(now, current_deviation))
        return None

    print("{} deviation ok = {}".format(now, current_deviation))

    push_detected = False

    # look back 15 seconds and see if push detected AND stable prior value was 100.500g higher than latest stable value
    for i in range(POUR_TEST_SECONDS):
        stats_record = stats_buffer.get(i)
        if stats_record is None:
            continue

        stats = stats_record["value"]

        # skip if we have no stats for current period
        if ( stats is None or
             stats["median"] is None or
             stats["deviation"] is None or
             stats["duration"] is None or
             stats["duration"] < 0.5 or
             stats["sample_count"] is None or
             stats["sample_count"] < 5 ):
            continue

        # check for push
        if not push_detected and stats["median"] >  current_median + 2000:
            push_detected = True
            print("{} push detected at {}".format(now, stats_record["ts"]))
            continue

        # check for higher level of coffee before push
        med_delta = stats["median"] - current_median

        if push_detected and stats["deviation"] < 30 and med_delta > 100 and med_delta < 500:
            print(stats)
            print("{} EVENT POURED amount={:.1f} from {}".format(now, med_delta, stats_record["ts"]))
            e.put(now, "EVENT_POURED")
            return "EVENT_POURED"

    return None

def process_sample(ts,value):
    t.put(ts,value)
    pour_test(t,s)

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

r.play(process_sample) #, realtime=True)

print("\n Events")

for i in range(e.size):
    ev = e.get(i)
    if not ev is None:
        print(ev)

