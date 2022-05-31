import numpy as np
import json
import time
import traceback
import mpit.utils.preprocessing as preproc
import mpit.skeleton as skeleton
import mpit.algorithms as algorithms
import matplotlib.pyplot as plt


def plot_positions(positions_one_point):
    t = np.copy(positions_one_point['t'])
    skeletons = positions_one_point['skeletons']
    plt.subplot(3, 1, 1)
    for id in skeletons:
        plt.plot(t, skeletons[str(id)]['px'], label=id)
    plt.xlabel('time')
    plt.ylabel('position x')
    plt.title('Point position in x over time')
    plt.subplot(3, 1, 2)
    for id in skeletons:
        plt.plot(t, skeletons[str(id)]['py'], label=id)
    plt.xlabel('time')
    plt.ylabel('position y')
    plt.title('Point position in y over time')
    plt.subplot(3, 1, 3)
    for id in skeletons:
        plt.plot(t, skeletons[str(id)]['pz'], label=id)
    plt.xlabel('time')
    plt.ylabel('position z')
    plt.title('Point position in z over time')
    plt.tight_layout()


def bounded_in_list(items_list, start_ts, end_ts):
    matches = []
    for item in items_list:
        if start_ts <= item['timestamp'] < end_ts:
            matches.append(item)
        elif item['timestamp'] >= end_ts:
            break
    return matches


if __name__ == "__main__":
    skeleton_min_duration = 5
    verbose = 0
    # Open JSONs
    with open("Data/reidentification/case3_1/skeleton.json", "r") as fs:
        skeleton_list = json.load(fs)
    with open("Data/reidentification/case3_1/accel.json", "r") as fs:
        accel_list = json.load(fs)
    # Get first and last timestamp
    first_ts = skeleton_list[0]['timestamp']
    last_ts = skeleton_list[-1]['timestamp']
    # Do PIT per chuck
    associations_list = []
    for ts in range(int(first_ts), int(last_ts), 10):
        skeletons = bounded_in_list(skeleton_list, ts, ts + 10)
        accels = bounded_in_list(accel_list, ts, ts + 10)
        try:
            associations_list.append(algorithms.identify_and_track(skeletons, accels))
        except Exception as err:
            print(traceback.format_exc())
            print("Error in the PIT:", err, "Please contact repositories authors: "
                                            "https://github.com/matteo-bastico/Multisensor-PIT")
    # Graphical visualization of PIT
    plt.figure(figsize=(8, 4))
    wrist_points = preproc.get_positions_one_point(skeleton_list, 7, 18, verbose=0)
    elbow_points = preproc.get_positions_one_point(skeleton_list, 6, 18, verbose=0)
    wrist_points = skeleton.filter_skeletons(wrist_points, min_duration=skeleton_min_duration, verbose=verbose)
    elbow_points = skeleton.filter_skeletons(elbow_points, min_duration=skeleton_min_duration, verbose=verbose)
    wrist_points, elbow_points = skeleton.post_process_xy(wrist_points, elbow_points,
                                                          smooth_filter="savgol",
                                                          window=7,
                                                          poly=1,
                                                          verbose=verbose)
    t = np.copy(wrist_points['t'])
    skeletons = wrist_points['skeletons']
    for id in skeletons:
        plt.plot(t, skeletons[str(id)]['px'], label=id)
    y_min, y_max = plt.gca().get_ylim()
    for associations in associations_list:
        plt.axvline(x=associations[0]['ts_end'], color="r")
        i = 0
        for association in associations:
            plt.text(association['ts_start'], (0.8-i)*y_max,
                     str(association['skeleton_id']) + "->" + str(association['bracelet_id']), fontsize=8)
            i += 0.1
    plt.legend()
    plt.show()
