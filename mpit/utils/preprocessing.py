import numpy as np


def get_positions_one_point(frames, point, tot_points, verbose=1):
    """ Extract from full skeletons sequences of the point of interest

    :param frames: list of skeletons frames as
                   [{'skeletons':{'<id_sk1>': {'confidences':[<values>],
                                              'joints':[<values>],
                                              'joints3D':[<values>]},
                                   '<id_sk2>': {...}, ...
                                  }
                      'timestamp': <value>},
                      ...
                   ]
    :param point: number of the point to get (int)
    :param tot_points: number of points per skeleton depending on the camera
    :param verbose: if >1 print logs
    :return: positions of one point in numpy format structured as following dict
             {'t': np.array(values),
              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                        'py': np.array(values),
                                        'pz': np.array(values)},
                             <id_sk2>: {...}, ...
                             }
              }

    """

    t = []  # Timestamps
    skeletons_point = {}  # Dict for skeletons point
    # For each frame in the sequence
    for id_fr, frame in enumerate(frames):
        t.append(frame['timestamp'])  # Add timestamp to list
        skeletons = frame["skeletons"]
        # For each skeleton in the frame create a vector with the positions of the wrist in x, y and z
        for id_sk in skeletons:
            # Check if data are corrupted, if so the order of points cannot be inferred
            if len(skeletons[id_sk]['joints3D']) == tot_points:
                insert_point = skeletons[id_sk]['joints3D'][point]  # Point to add to the sequence
            else:
                insert_point = [np.nan, np.nan, np.nan]
            # If id_sk has already data related
            if id_sk in skeletons_point.keys():
                skeletons_point[id_sk]['px'] = np.append(skeletons_point[id_sk]['px'],
                                                         insert_point[0])
                skeletons_point[id_sk]['py'] = np.append(skeletons_point[id_sk]['py'],
                                                         insert_point[1])
                skeletons_point[id_sk]['pz'] = np.append(skeletons_point[id_sk]['pz'],
                                                         insert_point[2])
            # Otherwise, add new id_sk to skeletons_point
            else:
                skeletons_point[id_sk] = {}
                # If first frame
                if id_fr == 0:
                    skeletons_point[id_sk]['px'] = np.array(insert_point[0], dtype=np.float)
                    skeletons_point[id_sk]['py'] = np.array(insert_point[1], dtype=np.float)
                    skeletons_point[id_sk]['pz'] = np.array(insert_point[2], dtype=np.float)
                else:
                    # Generate a vector of null values till id_fr-1
                    skeletons_point[id_sk]['px'] = np.append([np.nan] * (id_fr - 1), insert_point[0])
                    skeletons_point[id_sk]['py'] = np.append([np.nan] * (id_fr - 1), insert_point[1])
                    skeletons_point[id_sk]['pz'] = np.append([np.nan] * (id_fr - 1), insert_point[2])
    t = np.array(t)
    # Check if some array is not full, only for x because the others coordinates are the same
    # Fill with np.nan values the missing skeletons
    for id_sk in skeletons_point:
        size = skeletons_point[id_sk]['px'].size
        if t.size != size:
            skeletons_point[id_sk]['px'] = np.append(skeletons_point[id_sk]['px'],
                                                     [np.nan] * (t.size - size))
            skeletons_point[id_sk]['py'] = np.append(skeletons_point[id_sk]['py'],
                                                     [np.nan] * (t.size - size))
            skeletons_point[id_sk]['pz'] = np.append(skeletons_point[id_sk]['pz'],
                                                     [np.nan] * (t.size - size))
        # Replace all -1 values (invalid points) with np.nan, this must be conditioned on z!
        skeletons_point[id_sk]['px'][skeletons_point[id_sk]['pz'] == -1] = np.nan
        skeletons_point[id_sk]['py'][skeletons_point[id_sk]['pz'] == -1] = np.nan
        skeletons_point[id_sk]['pz'][skeletons_point[id_sk]['pz'] == -1] = np.nan
    if verbose >= 1:
        print('Skeletons extracted correctly, ' + str(skeletons_point.keys().__len__()) +
              ' skeleton(s) identifiers found in the sequence')
        print('------------------------------------------------------------')
    return {'t': t, 'skeletons': skeletons_point}


def get_accelerations(accelerations, verbose=1):
    """ Change format of accelerations for faster computation

    :param accelerations: list of acceleration measurements as
                                [{'x': <value>,
                                  'y': <value>,
                                  'z': <value>,
                                  'timestamp': <value>,
                                  'id': <value>}, ...
                                ]
    :param verbose: if >1 print logs
    :return: dictionary as
            {<id_br1>: {'ax': np.array(values),
                        'ay': np.array(values),
                        'az': np.array(values),
                        't': np.array(values)}
                        }
            <id_br2>: {...}, ...
            }
    """

    accel_dict = {}
    for sample in accelerations:
        # If id_br has already data related
        if sample['id'] in accel_dict.keys():
            accel_dict[sample['id']]['ax'] = np.append(accel_dict[sample['id']]['ax'], sample['x'])
            accel_dict[sample['id']]['ay'] = np.append(accel_dict[sample['id']]['ay'], sample['y'])
            accel_dict[sample['id']]['az'] = np.append(accel_dict[sample['id']]['az'], sample['z'])
            accel_dict[sample['id']]['t'] = np.append(accel_dict[sample['id']]['t'], sample['timestamp'])
        # Otherwise, add new id_br to accel_dict
        else:
            accel_dict[sample['id']] = {}
            accel_dict[sample['id']]['ax'] = np.array(sample['x'])
            accel_dict[sample['id']]['ay'] = np.array(sample['y'])
            accel_dict[sample['id']]['az'] = np.array(sample['z'])
            accel_dict[sample['id']]['t'] = np.array(sample['timestamp'])
    if verbose >= 1:
        print('Accelerations extracted correctly, ' + str(accel_dict.keys().__len__()) +
              ' bracelet(s) identifiers found in the sequence')
        print('------------------------------------------------------------')
    return accel_dict
