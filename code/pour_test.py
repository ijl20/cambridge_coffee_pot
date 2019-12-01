
POUR_TEST_SECONDS = 15
def pour_test(time_buffer, offset):
    now = time_buffer.get(0)["ts"]
    print("now=", now)
    seconds = []
    current_offset = offset
    for i in range(POUR_TEST_SECONDS):
        # get one-second median
        median, next_offset, sample_count = time_buffer.median(current_offset, 1)
        dev, next_offset, sample_count = time_buffer.deviation(current_offset, 1, median)
        current_offset = next_offset
        seconds.append( { "med": median, "dev": dev, "count": sample_count } )

    print(seconds)

    # COFFEE_POURED == False if current 1 second weight not stable
    if seconds[0]["dev"] > 30:
        print("not stable now")
        return None

    push_detected = False
    for i in range(1, POUR_TEST_SECONDS):

        if seconds[i]["med"] > seconds[0]["med"] + 2000 and seconds[i]["count"] > 4:
            push_detected = True
            print("push detected at {}".format(i))
            continue

        med_delta = seconds[i]["med"] - seconds[0]["med"]
        if push_detected and seconds[i]["dev"] < 30 and med_delta > 100 and med_delta < 500:
            print("EVENT POURED {:.1f} from {} at {}".format( med_delta, i, now - time_buffer.get(offset)["ts"]))
            return "EVENT_POURED"

    return None

from classes.time_buffer import TimeBuffer

t = TimeBuffer()

t.load('../data/2019-11-22_readings.csv')

for i in range(200):
    pour_test(t, i)

