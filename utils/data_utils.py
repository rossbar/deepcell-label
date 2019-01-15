from io import BytesIO

import json
import numpy as np
import os
import pathlib
import tarfile
import tempfile

def generate_lineage(tracked, daughters):
    """
    generates dictionary equivalent to `lineage.json` in .trk files.
    these WILL be missing `capped` and `frame_div`, since there is no way
    to always correctly infer this information.
    """

    lineage = {}

    # fill in `label` & `frames`
    for frame in range(tracked.shape[0]):
        X = tracked[frame]
        for cell in map(int, np.unique(X)):
            if cell == 0:
                continue
            if cell not in lineage:
                lineage[cell] = {"label": cell,
                                 "frames": [frame],
                                 "parent": None,
                                 "daughters": list(map(int, daughters[cell]))}
            else:
                lineage[cell]["frames"].append(frame)

    # fill in `parent` & `daughters`
    for cell, track in lineage.items():
        for c in track["daughters"]:
            lineage[c]["parent"] = cell

    return lineage


def generate_lineages(tracked, daughters):
    """
    generates dictionary equivalent to `lineages.json` in .trks files.
    """
    return [generate_lineage(tracked[batch], daughters[batch])
            for batch in range(tracked.shape[0])]


def npz_and_kids_to_trks(filename, filename_kids, outfilename):
    data = np.load(filename)
    kids = np.load(filename_kids)

    raw = data["X"]
    tracked = data["y"]

    # convert kids["daughters"] to a list of dicts
    daughters = []
    for daughters_batch in kids["daughters"]:
        d = {}
        for i, lst in enumerate(daughters_batch):
            if i == 0:
                continue
            d[i] = list(map(int, lst))
        daughters.append(d)

    lineages = generate_lineages(tracked, daughters)

    save_trks(outfilename, lineages, raw, tracked)


def trk_folder_to_trks(dirname, trks_filename):
    lineages = []
    raw = []
    tracked = []

    for filename in os.listdir(dirname):
        trk = load_trk(os.path.join(dirname, filename))
        lineages.append(trk["lineage"])
        raw.append(trk["raw"])
        tracked.append(trk["tracked"])

    save_triks(trks_filename, lineages, raw, tracked)


def trks_to_trk_folder(trks_filename, dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    else:
        raise ValueError("directory '{}' exists".format(dirname))

    trks = load_trks(trks_filename)
    num_batches = len(trks["lineages"])
    num_zeros = len(str(num_batches))
    for i, (lineage, raw, tracked) in enumerate(zip(trks["lineages"],
                                      trks["raw"],
                                      trks["tracked"])):
        i = str(i).zfill(num_zeros)
        save_trk(os.path.join(dirname, "batch_{}.trk".format(i)),
                 lineage,
                 raw,
                 tracked)


def save_trks(filename, lineages, raw, tracked):
    if not filename.endswith(".trks"):
        raise ValueError("filename must end with '.trks'")

    with tarfile.open(filename, "w") as trks:
        with tempfile.NamedTemporaryFile("w") as lineages_file:
            json.dump(lineages, lineages_file, indent=1)
            lineages_file.flush()
            trks.add(lineages_file.name, "lineages.json")

        with tempfile.NamedTemporaryFile() as raw_file:
            np.save(raw_file, raw)
            raw_file.flush()
            trks.add(raw_file.name, "raw.npy")

        with tempfile.NamedTemporaryFile() as tracked_file:
            np.save(tracked_file, tracked)
            tracked_file.flush()
            trks.add(tracked_file.name, "tracked.npy")


def save_trk(filename, lineage, raw, tracked):
    if not filename.endswith(".trk"):
        raise ValueError("filename must end with '.trk'")

    with tarfile.open(filename, "w") as trks:
        with tempfile.NamedTemporaryFile("w") as lineage_file:
            json.dump(lineage, lineage_file, indent=1)
            lineage_file.flush()
            trks.add(lineage_file.name, "lineage.json")

        with tempfile.NamedTemporaryFile() as raw_file:
            np.save(raw_file, raw)
            raw_file.flush()
            trks.add(raw_file.name, "raw.npy")

        with tempfile.NamedTemporaryFile() as tracked_file:
            np.save(tracked_file, tracked)
            tracked_file.flush()
            trks.add(tracked_file.name, "tracked.npy")


def load_trks(trks_file):
    with tarfile.open(trks_file, "r") as trks:
        # trks.extractfile opens a file in bytes mode, json can't use bytes.
        lineages = json.loads(
                trks.extractfile(
                    trks.getmember("lineages.json")).read().decode())

        # numpy can't read these from disk...
        array_file = BytesIO()
        array_file.write(trks.extractfile("raw.npy").read())
        array_file.seek(0)
        raw = np.load(array_file)
        array_file.close()

        array_file = BytesIO()
        array_file.write(trks.extractfile("tracked.npy").read())
        array_file.seek(0)
        tracked = np.load(array_file)
        array_file.close()

    # JSON only allows strings as keys, so we convert them back to ints here
    for i, tracks in enumerate(lineages):
        lineages[i] = {int(k): v for k, v in tracks.items()}

    return {"lineages": lineages, "raw": raw, "tracked": tracked}


def load_trk(filename):
    with tarfile.open(filename, "r") as trks:
        # trks.extractfile opens a file in bytes mode, json can't use bytes.
        lineage = json.loads(
                trks.extractfile(
                    trks.getmember("lineage.json")).read().decode())

        # numpy can't read these from disk...
        array_file = BytesIO()
        array_file.write(trks.extractfile("raw.npy").read())
        array_file.seek(0)
        raw = np.load(array_file)
        array_file.close()

        array_file = BytesIO()
        array_file.write(trks.extractfile("tracked.npy").read())
        array_file.seek(0)
        tracked = np.load(array_file)
        array_file.close()

    # JSON only allows strings as keys, so we convert them back to ints here
    lineage = {int(k): v for k, v in lineage.items()}

    return {"lineage": lineage, "raw": raw, "tracked": tracked}

