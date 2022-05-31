import mpit.utils.preprocessing as preproc
import mpit.utils.conversion as conversion
import mpit.utils.filtering as filtering
import mpit.core as core
import mpit.skeleton as skeleton


def identify_and_track(skeletons_frames, accelerations_dict, camera="Intel",
                       acceleration_smooth_window=35, acceleration_smooth_poly=1,
                       skeleton_min_duration=5, skeleton_smooth_filter="savgol",
                       skeleton_smooth_window=7, skeleton_smooth_poly=1,
                       direction_smooth_filter="savgol",
                       direction_smooth_window=5, direction_smooth_poly=1,
                       conversion_smoothing_window=3, conversion_smoothing_poly=1,
                       camera_angle=0, similarity_weight=0.7, verbose=0):
    assert camera == "Intel" or camera == "Kinect", "Type of camera not valid (Intel or Kinect)"
    # Select points
    if camera == 'Intel':
        elbow = 6
        wrist = 7
        tot_points = 18
    elif camera == 'Kinect':
        elbow = 5
        wrist = 6
        tot_points = 32
    wrist_points = preproc.get_positions_one_point(skeletons_frames, wrist, tot_points, verbose=verbose)
    elbow_points = preproc.get_positions_one_point(skeletons_frames, elbow, tot_points, verbose=verbose)
    accelerations = preproc.get_accelerations(accelerations_dict, verbose=verbose)
    accelerations = filtering.smooth_accelerations(accelerations, window=acceleration_smooth_window,
                                                   poly=acceleration_smooth_poly)
    wrist_points = skeleton.filter_skeletons(wrist_points, min_duration=skeleton_min_duration, verbose=verbose)
    elbow_points = skeleton.filter_skeletons(elbow_points, min_duration=skeleton_min_duration, verbose=verbose)
    wrist_points, elbow_points = skeleton.post_process_xy(wrist_points, elbow_points,
                                                          smooth_filter=skeleton_smooth_filter,
                                                          window=skeleton_smooth_window,
                                                          poly=skeleton_smooth_poly,
                                                          verbose=verbose)
    wrist_points, elbow_points, directions = skeleton.get_directions(wrist_points,elbow_points,
                                                                     smooth_filter=direction_smooth_filter,
                                                                     window=direction_smooth_window,
                                                                     poly=direction_smooth_poly,
                                                                     verbose=verbose)
    skel_accel = conversion.get_skeletons_point_accelerations(wrist_points,
                                                              window=conversion_smoothing_window,
                                                              poly=conversion_smoothing_poly,
                                                              verbose=verbose)
    skel_accel_gravity = core.add_gravity_to_skeletons_accelerations(skel_accel, camera_angle, verbose=verbose)
    skel_accel_rotated = core.get_skeleton_accelerations_rotated(skel_accel_gravity, directions, verbose=verbose)
    associations = core.do_association(skel_accel_rotated, accelerations, similarity_weight, verbose=verbose)
    return associations
