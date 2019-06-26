# Takes a JSON file and outputs simulated JSON files for 12 hours of stream by default
# To be run in Simulation Node, connected to S3(?)
# DON'T RUN IN LOCAL

import datetime as dt
import time
import json
import numpy as np
import boto3
import os
# from cassandra.cluster import Cluster


def write_to_s3(timestamp, website, streamer, current_subscriber_count):
    key = timestamp + '_' + website + '_' + streamer
    with open('./simulation_dump/' + key + '.json', 'w+') as g:
        json.dump({'total': current_subscriber_count}, g)
    # s3.put_object(Bucket=bucket_name, Key=key, Body=json.dump({streamer: current_subscriber_count}))
    s3.upload_file('./simulation_dump/' + key + '.json', bucket_name, key + '.json')
    os.remove('./simulation_dump/' + key + '.json')


def generate_data(streamer, data, time_format='%Y-%m-%d_%H-%M-%S',
                  # final_date=dt.datetime.today() + dt.timedelta(hours=1)):
                  final_date=dt.datetime.today() + dt.timedelta(minutes=10)):
    try:
        final_datetime = dt.datetime.strptime(final_date, time_format)
    except TypeError:
        final_datetime = final_date
    for website, (creation_date, current_subscriber_count) in data.items():
        creation_datetime = dt.datetime.today()

        number_of_simulations = int(abs(creation_datetime - final_datetime).total_seconds()//2)

        for timestamp, simulated_subscriber_count in random_walk_generator(creation_datetime, number_of_simulations,
                                                                           current_subscriber_count, time_format):
            write_to_s3(timestamp, website, streamer, simulated_subscriber_count)


def random_walk_generator(creation_datetime, number_of_simulations, current_subscriber_count, time_format='%Y-%m-%d'):
    # we generate bounded random walk with an std of 1% of the max. We assume initial subscriber_count is 0
    random_steps = bounded_random_walk(number_of_simulations, 0, current_subscriber_count,
                                       current_subscriber_count * 0.01)
    for i, simulated_subscriber_count in enumerate(random_steps):
        yield (dt.datetime.strftime(creation_datetime + dt.timedelta(seconds=i), time_format),
               int(simulated_subscriber_count))


def bounded_random_walk(length, start, end, std, lower_bound=0, upper_bound=np.inf):
    assert (lower_bound <= start and lower_bound <= end)
    assert (start <= upper_bound and end <= upper_bound)

    bounds = upper_bound - lower_bound

    rand = (std * (np.random.random(length) - 0.5)).cumsum()
    rand_trend = np.linspace(rand[0], rand[-1], length)

    rand_deltas = (rand - rand_trend)
    rand_deltas /= np.max([1, (rand_deltas.max()-rand_deltas.min())/bounds])

    trend_line = np.linspace(start, end, length)
    upper_bound_delta = upper_bound - trend_line
    lower_bound_delta = lower_bound - trend_line

    upper_slips_mask = (rand_deltas-upper_bound_delta) >= 0
    upper_deltas = rand_deltas - upper_bound_delta
    rand_deltas[upper_slips_mask] = (upper_bound_delta - upper_deltas)[upper_slips_mask]

    lower_slips_mask = (lower_bound_delta-rand_deltas) >= 0
    lower_deltas = lower_bound_delta - rand_deltas
    rand_deltas[lower_slips_mask] = (lower_bound_delta + lower_deltas)[lower_slips_mask]

    return trend_line + rand_deltas


t = time.time()
t1 = time.time()
s3 = boto3.client('s3')
bucket_name = 'insight-api-dumps'

with open('random_accounts.json') as f:
    accounts_dict = json.load(f)
j = 1
for streamer_name, streamer_data in accounts_dict.items():
    generate_data(streamer_name, streamer_data)
    print(streamer_name + ' ' + str(j) + '  DONE.')
    print(time.time() - t1)
    t1 = 0
print(time.time() - t)
print('LIVE DATA DONE.')
