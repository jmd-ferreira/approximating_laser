from datetime import datetime
import os
from stream.teststream import TestStream
from evalunit.program import Program


def create_stream(f_name):
    stream = dict()
    event_counter = dict()
    measure_counter = dict()
    timestamp = 0
    atom_counter = 0
    sectors = set()
    with open(f_name, "r") as file:
        for line in file.readlines():
            the_split = line.split(":[")
            atoms_list = list(the_split[1].split("]")[0].split('"'))[1::2]
            """for i in range(0, len(atoms_list)):
                atom = atoms_list[i]
                pred_split = atom.split("(")
                params = pred_split[1].split(")")[0].split(",")
                if not pred_split[0] == "weather":
                    sectors.add(int(params[len(params) - 1]))
                event_counter[pred_split[0]] = event_counter.get(pred_split[0], 0) + 1
                measure_counter[pred_split[0]] = measure_counter.get(pred_split[0], dict())
                if params[1] == "":
                    measure_val = 0
                else:
                    measure_val = int(float(params[1]))
                attrb_vals = measure_counter[pred_split[0]].get(params[0], [measure_val, measure_val, 0, 0])
                if measure_val > attrb_vals[1]:
                    attrb_vals[1] = measure_val
                if measure_val < attrb_vals[0]:
                    attrb_vals[0] = measure_val
                attrb_vals[2] += 1  # len
                attrb_vals[3] += measure_val  # sum

                measure_counter[pred_split[0]][params[0]] = attrb_vals
                atom_counter += 1"""
            stream[int(the_split[0])] = atoms_list
            timestamp += 1

    print("Total number of atoms = {}".format(atom_counter))
    for atom in event_counter.items():
        print("Avg num of " + atom[0].upper() + " atoms/timestamp in stream = " + str(float(atom[1]) / timestamp))
    for items in measure_counter.items():
        print("Event: {}".format(items[0].upper()))
        for measure in items[1].items():
            print("Measure: {} --> min_value: {}; max_value: {}; avg: {}".format(measure[0].upper(), measure[1][0],
                                                                                 measure[1][1],
                                                                                 round(measure[1][3] / measure[1][2],
                                                                                       2)))
            atom_counter -= measure[1][2]
    print("Sectors list: {}\n".format(str(sectors)))
    assert atom_counter == 0
    return stream



def query_one(filename, output_stream):
    stream = create_stream(filename)

    rules = [
        "traff_inc(MES,SEC) :- time_win(9, 0, 1, @(T, traffic(MES,VAL,SEC)))"
        "and time_win(8, 0, 1, @(T1, traffic(MES,VAL2,SEC)))"
        "and MATH(+,RT,T,1) and COMP(==, RT, T1)"
        "and COMP(>=, VAL, VAL2) ",

        "poll_dec(MES,SEC) :- time_win(9, 0, 1, @(T, pollution(MES,VAL,SEC)))"
        "and time_win(8, 0, 1, @(T1, pollution(MES,VAL2,SEC)))"
        "and MATH(+,RT,T,1) and COMP(==, RT, T1)"
        "and COMP(<=, VAL, VAL2) ",

        "traff_dec(MES,SEC) :- time_win(9, 0, 1, @(T, traffic(MES,VAL,SEC)))"
        "and time_win(8, 0, 1, @(T1, traffic(MES,VAL2,SEC)))"
        "and MATH(+,RT,T,1) and COMP(==, RT, T1)"
        "and COMP(<=, VAL, VAL2) ",

        "traff_low(MES,SEC) :- time_win(9, 0, 1, diamond(traffic(MES,VAL,SEC)))"
        "and COMP(>=,VAL, 10) and COMP(<=,VAL,11)",

        "poll_low(MES,SEC) :- time_win(9, 0, 1, diamond(pollution(MES,VAL,SEC)))"
        "and COMP(>=,VAL, 0) and COMP(<=,VAL,15)",

        "urban_area(SEC) :- time_win(9, 0, 1, diamond(traff_inc(MES, SEC)))"
        "and time_win(9, 0, 1, diamond(poll_dec(MES10,SEC)))"
        "and time_win(9, 0, 1, diamond(poll_low(MES2,SEC)))"
        "and time_win(9, 0, 1, diamond(traff_low(MES4,SEC)))"
        "and COMP(s!=, MES, MES10)",
    ]

    ti, tf = min(stream.keys()), max(stream.keys())
    s = TestStream(stream, ti, tf)
    prog = Program(rules, s)
    total_time = 0
    positive_t = 0
    for t in range(0, tf):
        init_t = datetime.now()
        res, tuples = prog.evaluate(t)
        # print(str(tuples))
        tups = set()
        final_t = datetime.now()
        if t > ti:
            total_time += (final_t - init_t).total_seconds()
            print("Timestamp: {};  Seconds to evaluate: {};".format(t, (final_t - init_t).total_seconds()))

            if len(tuples) > 0 and res:
                for tup in tuples.items():
                    tups = filter(lambda x: "city" in x, tup[1])
                    output_stream.write(str(tup[0]) + ": " + str(tup[1]) + "\n")
                    if len(tups) > 0:
                        positive_t += 1

            if t % 10 == 0:
                print("Average time per timestamp (secs): {};    Expected remained time (mins): {}".format(
                    total_time / (t - ti), ((total_time / (t - ti)) * (tf - t)) / 60))
                print("Positive ratio: {}".format(float(positive_t) / (t - ti)))
    return tf - ti

laser_folder = os.getcwd() + "/"
input_folder = laser_folder + "laser_input/"
output_folder = laser_folder + "q4_output/"
counter = 9
window_num = 0
query_dict = dict()
init_time = datetime.now()
for filename in os.listdir(input_folder):
    if counter == 0:
        break

    filename = "laser{}.txt".format(counter)
    print(filename)
    with open(output_folder + "output_" + filename, "w") as out:
        window_num += query_one(input_folder + filename, out)

    counter -= 1
end_time = datetime.now()
print(window_num)
print("\nnumber of window tested: {}\nTotal time in exec: {}\n".format(window_num,
                                                                       (end_time - init_time).total_seconds()))
