import similaritymeasures

import numpy as np


def compare_accel(skeleton_accel, bracelet_accel):
    """
    
    :param skeleton_accel: dictionary of accelerations in the following format:
                             { 't': <timestamps>,
                               'skeletons':{'<id_br1>':{'u': np.array(values),
                                                        'v': np.array(values),
                                                        'w': np.array(values),
                                                        'au: np.array(values),
                                                        'av': np.array(values),
                                                        'aw': np.array(values)},
                                                         ... }
                            }
    :param bracelet_accel: accelerations: dictionary as
                              {<id_br1>: {'ax': np.array(values),
                                          'ay': np.array(values),
                                          'az': np.array(values),
                                          't': np.array(values)}
                                          }
                              <id_br2>: {...}, ...
                              }
    :return: dict with DTW similarities
    """
    skeletons_ts = skeleton_accel['t']
    reid_dict = {}
    for id_sk in skeleton_accel['skeletons']:
        valids = np.where(~np.isnan(skeleton_accel['skeletons'][id_sk]['au']))
        if len(valids) > 0:
            reid_dict[id_sk] = {}
            for id_brac in bracelet_accel:
                if len(bracelet_accel[id_brac]['t']) > 0:
                    sk_data = np.zeros((len(valids[0]), 2))
                    sk_data[:, 0] = skeletons_ts[valids]
                    sk_data[:, 1] = skeleton_accel['skeletons'][id_sk]['au'][valids]
                    bracelet_data = np.zeros((len(bracelet_accel[id_brac]['t']), 2))
                    bracelet_data[:, 0] = bracelet_accel[id_brac]['t']
                    bracelet_data[:, 1] = bracelet_accel[id_brac]['ax']
                    dtw, d = similaritymeasures.dtw(sk_data, bracelet_data)
                    reid_dict[id_sk][id_brac] = dtw
                else:
                    reid_dict[id_sk][id_brac] = np.nan
    return reid_dict


def compare_accel_der(skeleton_accel, bracelet_accel):
    """
    
    :param skeleton_accel: dictionary of accelerations in the following format:
                             { 't': <timestamps>,
                               'skeletons':{'<id_br1>':{'u': np.array(values),
                                                        'v': np.array(values),
                                                        'w': np.array(values),
                                                        'au: np.array(values),
                                                        'av': np.array(values),
                                                        'aw': np.array(values)},
                                                         ... }
                            }
    :param bracelet_accel: accelerations: dictionary as
                              {<id_br1>: {'ax': np.array(values),
                                          'ay': np.array(values),
                                          'az': np.array(values),
                                          't': np.array(values)}
                                          }
                              <id_br2>: {...}, ...
                              }
    :return: dict with DTW similarities
    """
    # Derivative
    for id_sk in skeleton_accel['skeletons']:
        # Diff skeleton accels only in u
        valids = np.where(~np.isnan(skeleton_accel['skeletons'][id_sk]['au']))
        der_valids = np.diff(skeleton_accel['skeletons'][id_sk]['au'][valids]) / np.diff(skeleton_accel['t'][valids])
        der_tot = np.empty(len(skeleton_accel['skeletons'][id_sk]['au']) - 1)
        der_tot[:] = np.nan
        der_tot[valids[0][:-1]] = der_valids
        skeleton_accel['skeletons'][id_sk]['au'] = der_tot
    skeleton_accel['t'] = skeleton_accel['t'][:-1]
    invalid_br = []
    for id_br in bracelet_accel:
        # Diff bracelet accel only in x
        if 0 in np.diff(bracelet_accel[id_br]['t']):
            print("WARNING: Bracelet data of %s contain equal timestamps, removed"
                  " from derivative comparison." % str(id_br))
            invalid_br.append(id_br)
        else:
            bracelet_accel[id_br]['ax'] = np.diff(bracelet_accel[id_br]['ax']) / np.diff(bracelet_accel[id_br]['t'])
            bracelet_accel[id_br]['t'] = bracelet_accel[id_br]['t'][:-1]
    # Remove invalid bracelets
    for id_br in invalid_br:
        del bracelet_accel[id_br]
    return compare_accel(skeleton_accel, bracelet_accel)
