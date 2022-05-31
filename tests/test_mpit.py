import numpy as np
import argparse
import json
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--skeleton-path", type=str, default="Data/reidentification/case1_1/skeleton.json",
                        help="Skeleton data in the specified format")
    parser.add_argument("-a", "--accelerometer-path", type=str, default="Data/reidentification/case1_1/accel.json",
                        help="Accelerometer data in the specified format")
    parser.add_argument("-w", "--window", default=10, type=int,
                        help="Chunk size in seconds.")
    parser.add_argument("-c", "--camera", default="Intel", type=str,
                        help="Camera acquiring skeleton data (Intel or Kinect")
    parser.add_argument("-asw", "--acceleration-smooth-window", default=35, type=int,
                        help="Smoothing window for acceleration.")
    parser.add_argument("-asp", "--acceleration-smooth-poly", default=1, type=int,
                        help="Smoothing poly for acceleration.")
    parser.add_argument("-smd", "--skeleton-min-duration", default=5, type=int,
                        help="Minimum duration for a skeleton to be considered valid")
    parser.add_argument("-ssf", "--skeleton-smooth-filter", default="savgol", type=str,
                        help="Smoothing filter for skeletons")
    parser.add_argument("-ssw", "--skeleton-smooth-window", default=7, type=int,
                        help="Smoothing window for skeletons.")
    parser.add_argument("-ssp", "--skeleton-smooth-poly", default=1, type=int,
                        help="Smoothing poly for skeletons.")
    parser.add_argument("-dsw", "--direction-smooth-window", default=5, type=int,
                        help="Smoothing window for directions.")
    parser.add_argument("-dsp", "--direction-smooth-poly", default=1, type=int,
                        help="Smoothing poly for directions.")
    parser.add_argument("-dsf", "--direction-smooth-filter", default="savgol", type=str,
                        help="Smoothing filter for skeletons")
    parser.add_argument("-csw", "--conversion-smooth-window", default=3, type=int,
                        help="Smoothing window for conversion of skeletons positions to accelerations.")
    parser.add_argument("-csp", "--conversion-smooth-poly", default=1, type=int,
                        help="Smoothing window for conversion of skeletons positions to accelerations.")
    parser.add_argument("-ca", "--camera-angle", default=0, type=int,
                        help="Camera rotation angle on the y-axis.")
    parser.add_argument("-v", "--verbose", default=0, type=int,
                        help=">=1 for console logs.")
    parser.add_argument("-sw", "--similarity-weight", default=0.7, type=float,
                        help="Weight for similarities measures.")
    args = parser.parse_args()
    # Open JSONs
    with open(args.skeleton_path, "r") as fs:
        skeleton_list = json.load(fs)
    with open(args.accelerometer_path, "r") as fs:
        accel_list = json.load(fs)
    # Get first and last timestamp
    first_ts = skeleton_list[0]['timestamp']
    last_ts = skeleton_list[-1]['timestamp']
    # Do PIT per chuck
    associations_list = []
    for ts in range(int(first_ts), int(last_ts), args.window):
        skeletons = bounded_in_list(skeleton_list, ts, ts + args.window)
        accels = bounded_in_list(accel_list, ts, ts + args.window)
        try:
            associations = algorithms.identify_and_track(skeletons, accels,
                                                         camera=args.camera,
                                                         acceleration_smooth_window=args.acceleration_smooth_window,
                                                         acceleration_smooth_poly=args.acceleration_smooth_poly,
                                                         skeleton_min_duration=args.skeleton_min_duration,
                                                         skeleton_smooth_filter=args.skeleton_smooth_filter,
                                                         skeleton_smooth_window=args.skeleton_smooth_window,
                                                         skeleton_smooth_poly=args.skeleton_smooth_poly,
                                                         direction_smooth_filter=args.direction_smooth_filter,
                                                         direction_smooth_window=args.direction_smooth_window,
                                                         direction_smooth_poly=args.direction_smooth_poly,
                                                         conversion_smooth_window=args.conversion_smooth_window,
                                                         conversion_smooth_poly=args.conversion_smooth_poly,
                                                         camera_angle=args.camera_angle,
                                                         similarity_weight=args.similarity_weight,
                                                         verbose=args.verbose
                                                         )
            associations_list.append(associations)
        except Exception as err:
            print(traceback.format_exc())
            print("Error in the PIT:", err, "Please contact repositories authors: "
                                            "https://github.com/matteo-bastico/Multisensor-PIT")
    # Graphical visualization of PIT
    # Select points
    if args.camera == 'Intel':
        elbow = 6
        wrist = 7
        tot_points = 18
    elif args.camera == 'Kinect':
        elbow = 5
        wrist = 6
        tot_points = 32
    plt.figure(figsize=(8, 4))
    wrist_points = preproc.get_positions_one_point(skeleton_list, wrist, tot_points, verbose=args.verbose)
    elbow_points = preproc.get_positions_one_point(skeleton_list, elbow, tot_points, verbose=args.verbose)
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
        if len(associations) > 0:
            plt.axvline(x=associations[0]['ts_end'], color="r")
            i = 0
            for association in associations:
                plt.text(association['ts_start'], (0.8-i)*y_max,
                         str(association['skeleton_id']) + "->" + str(association['bracelet_id']), fontsize=8)
                i += 0.1
    plt.title("Skeletons x locations over time with associated bracelets")
    plt.legend(loc='lower left')
    plt.show()
